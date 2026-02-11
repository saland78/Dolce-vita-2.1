import asyncio
import logging
from database import db
from woocommerce import API
from models import OrderStatus
from datetime import datetime, timezone
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

def clean_html(raw_html):
    if not raw_html: return ""
    try:
        soup = BeautifulSoup(raw_html, "html.parser")
        return soup.get_text(separator=" ").strip()
    except:
        return str(raw_html)

async def sync_bakery(bakery):
    """
    Sync logic for ONE specific bakery.
    """
    bakery_id = str(bakery["_id"])
    url = bakery.get("wc_url")
    key = bakery.get("wc_consumer_key")
    secret = bakery.get("wc_consumer_secret")
    
    if not (url and key and secret):
        return

    try:
        wcapi = API(url=url, consumer_key=key, consumer_secret=secret, version="wc/v3", timeout=20)
        logger.info(f"Syncing Bakery: {bakery.get('name', 'Unknown')} ({bakery_id})")
        
        # --- PRODUCTS ---
        page = 1
        while True:
            r = wcapi.get("products", params={"per_page": 50, "page": page})
            if r.status_code != 200: break
            products = r.json()
            if not products: break
            
            for p in products:
                wc_id = str(p["id"])
                prod_data = {
                    "bakery_id": bakery_id, # TENANT
                    "name": p["name"],
                    "description": clean_html(p["short_description"] or p["description"]),
                    "price": float(p["price"] or 0),
                    "category": p["categories"][0]["name"] if p["categories"] else "General",
                    "image_url": p["images"][0]["src"] if p["images"] else None,
                    "sku": p.get("sku"),
                    "stock_status": p.get("stock_status"),
                    "source": "woocommerce",
                    "updated_at": datetime.now(timezone.utc)
                }
                
                # Upsert scoped to tenant
                # NOTE: wc_id is unique per WC installation, but multiple bakeries might have same ID if they reset or use same dump.
                # So we should use _id = wc_id? NO.
                # If we use _id = wc_id, Bakery A's product 15 will overwrite Bakery B's product 15.
                # We MUST make _id unique or composite.
                # BEST PRACTICE: Use custom _id = f"{bakery_id}_{wc_id}"
                
                custom_id = f"{bakery_id}_{wc_id}"
                
                await db.products.update_one(
                    {"_id": custom_id},
                    {"$set": prod_data},
                    upsert=True
                )
            page += 1

        # --- ORDERS ---
        r = wcapi.get("orders", params={"per_page": 20})
        if r.status_code == 200:
            orders = r.json()
            for o in orders:
                wc_id = str(o["id"])
                custom_id = f"{bakery_id}_{wc_id}" # Tenant-scoped ID
                
                existing = await db.orders.find_one({"_id": custom_id})
                
                items = []
                for item in o["line_items"]:
                    # Ensure product_id matches our tenant-scoped ID
                    p_id = f"{bakery_id}_{item['product_id']}"
                    items.append({
                        "product_id": p_id,
                        "product_name": item["name"],
                        "quantity": item["quantity"],
                        "unit_price": float(item["price"] or 0)
                    })

                status_map = {
                    "processing": OrderStatus.RECEIVED, 
                    "pending": OrderStatus.RECEIVED,
                    "completed": OrderStatus.DELIVERED,
                    "cancelled": OrderStatus.CANCELLED
                }
                
                wc_status = status_map.get(o["status"], OrderStatus.RECEIVED)
                final_status = wc_status
                
                if existing:
                    local = existing.get("status")
                    if local in [OrderStatus.IN_PRODUCTION, OrderStatus.READY] and wc_status == OrderStatus.RECEIVED:
                        final_status = local
                
                order_data = {
                    "bakery_id": bakery_id,
                    "customer_name": f"{o['billing']['first_name']} {o['billing']['last_name']}",
                    "customer_email": o["billing"]["email"],
                    "items": items,
                    "total_amount": float(o["total"]),
                    "status": final_status,
                    "created_at": datetime.fromisoformat(o["date_created_gmt"]).replace(tzinfo=timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                    "notes": clean_html(o.get("customer_note", ""))
                }
                if not existing: order_data["archived"] = False
                
                await db.orders.update_one({"_id": custom_id}, {"$set": order_data}, upsert=True)

    except Exception as e:
        logger.error(f"Error syncing bakery {bakery_id}: {e}")

async def sync_woocommerce():
    logger.info("Starting Multi-Tenant Sync Service...")
    while True:
        try:
            # Iterate all bakeries with credentials
            async for bakery in db.bakeries.find({"wc_url": {"$exists": True}}):
                await sync_bakery(bakery)
        except Exception as e:
            logger.error(f"Global Sync Loop Error: {e}")
        await asyncio.sleep(60)
