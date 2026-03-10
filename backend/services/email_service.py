import logging
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

async def get_smtp_settings(db: AsyncIOMotorDatabase, bakery_id: str):
    bakery = await db.bakeries.find_one({"_id": bakery_id})
    if not bakery:
        return None
    return bakery.get("smtp_settings")

class EmailService:

    @staticmethod
    async def send_email(smtp_cfg: dict, to_email: str, subject: str, html_body: str):
        if not smtp_cfg or not smtp_cfg.get("host"):
            logger.warning("SMTP non configurato — email non inviata")
            return False
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = smtp_cfg.get("from_email", smtp_cfg["username"])
            msg["To"] = to_email
            msg.attach(MIMEText(html_body, "html"))

            await aiosmtplib.send(
                msg,
                hostname=smtp_cfg["host"],
                port=int(smtp_cfg.get("port", 587)),
                username=smtp_cfg["username"],
                password=smtp_cfg["password"],
                start_tls=True,
            )
            logger.info(f"Email inviata a {to_email}: {subject}")
            return True
        except Exception as e:
            logger.error(f"Errore invio email a {to_email}: {e}")
            return False

    @staticmethod
    def _base_template(bakery_name: str, content: str) -> str:
        return f"""
        <html><body style="font-family:Georgia,serif;background:#fdf8f3;margin:0;padding:0;">
        <div style="max-width:560px;margin:40px auto;background:#fff;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(0,0,0,0.08);">
          <div style="background:#3d1a0e;padding:28px 32px;">
            <h1 style="color:#f5e6d0;margin:0;font-size:22px;letter-spacing:1px;">🥐 {bakery_name}</h1>
          </div>
          <div style="padding:32px;">
            {content}
          </div>
          <div style="background:#fdf8f3;padding:16px 32px;text-align:center;">
            <p style="color:#aaa;font-size:12px;margin:0;">© {bakery_name} — Gestito con DolceVita</p>
          </div>
        </div>
        </body></html>
        """

    @staticmethod
    async def send_order_confirmed(db, bakery_id: str, to_email: str, customer_name: str, order_id: str, items: list, total: float):
        smtp_cfg = await get_smtp_settings(db, bakery_id)
        bakery = await db.bakeries.find_one({"_id": bakery_id})
        bakery_name = bakery.get("name", "La Nostra Pasticceria") if bakery else "La Nostra Pasticceria"

        items_html = "".join([
            f'<tr><td style="padding:6px 0;color:#555;">{i.get("product_name","")}</td>'
            f'<td style="padding:6px 0;text-align:right;color:#3d1a0e;font-weight:bold;">x{i.get("quantity","")}</td></tr>'
            for i in items
        ])

        content = f"""
        <h2 style="color:#3d1a0e;margin-top:0;">Ciao {customer_name}! 🎉</h2>
        <p style="color:#555;line-height:1.6;">Il tuo ordine <strong>#{order_id[-6:].upper()}</strong> è stato ricevuto e preso in carico.</p>
        <table style="width:100%;border-top:1px solid #f0e8e0;margin:20px 0;">{items_html}</table>
        <div style="background:#fdf8f3;border-radius:8px;padding:16px;margin:20px 0;">
          <p style="margin:0;color:#3d1a0e;font-weight:bold;font-size:18px;">Totale: €{total:.2f}</p>
        </div>
        <p style="color:#555;">Ti avviseremo quando sarà pronto per il ritiro.</p>
        <p style="color:#888;font-size:13px;">A presto,<br><strong>{bakery_name}</strong></p>
        """
        html = EmailService._base_template(bakery_name, content)
        await EmailService.send_email(smtp_cfg, to_email, f"✅ Ordine #{order_id[-6:].upper()} confermato — {bakery_name}", html)

    @staticmethod
    async def send_order_ready(db, bakery_id: str, to_email: str, customer_name: str, order_id: str):
        smtp_cfg = await get_smtp_settings(db, bakery_id)
        bakery = await db.bakeries.find_one({"_id": bakery_id})
        bakery_name = bakery.get("name", "La Nostra Pasticceria") if bakery else "La Nostra Pasticceria"

        content = f"""
        <h2 style="color:#3d1a0e;margin-top:0;">È pronto! 🎂</h2>
        <p style="color:#555;line-height:1.6;">Ciao <strong>{customer_name}</strong>, il tuo ordine <strong>#{order_id[-6:].upper()}</strong> è pronto per il ritiro!</p>
        <div style="background:#f0fdf4;border:1px solid #86efac;border-radius:8px;padding:16px;margin:20px 0;">
          <p style="margin:0;color:#166534;font-weight:bold;">🟢 Puoi passare in pasticceria quando vuoi.</p>
        </div>
        <p style="color:#888;font-size:13px;">A presto,<br><strong>{bakery_name}</strong></p>
        """
        html = EmailService._base_template(bakery_name, content)
        await EmailService.send_email(smtp_cfg, to_email, f"🎂 Il tuo ordine è pronto! — {bakery_name}", html)

    @staticmethod
    async def send_order_ready_email(to_email: str, customer_name: str, order_id: str):
        """Backward compat — usato nel codice esistente, ora è un no-op silenzioso"""
        logger.info(f"[LEGACY] send_order_ready_email chiamato per {to_email} — usa send_order_ready con db")
