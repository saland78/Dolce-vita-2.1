import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class EmailService:
    @staticmethod
    async def send_order_ready_email(to_email: str, customer_name: str, order_id: str):
        """
        Mocks sending an email. In production, replace with Resend or SMTP.
        """
        if not to_email:
            logger.warning(f"Skipping email for order {order_id}: No email provided.")
            return

        subject = "Il tuo ordine è pronto! 🥐"
        body = f"""
        Ciao {customer_name},
        
        Siamo felici di informarti che il tuo ordine #{order_id[-6:].upper()} è pronto per il ritiro!
        
        Puoi passare in pasticceria quando vuoi.
        
        A presto,
        DolceVita Bakery Team
        """
        
        # LOGGING THE EMAIL (Simulation)
        print(f"\n[EMAIL MOCK] To: {to_email}")
        print(f"[EMAIL MOCK] Subject: {subject}")
        print(f"[EMAIL MOCK] Body: {body}\n")
        logger.info(f"Email sent to {to_email} for order {order_id}")
        return True
