import asyncio
import logging
from database import db
from woocommerce import API
from models import OrderStatus
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from services.parsers import parse_wc_order_meta, parse_wc_item_meta

logger = logging.getLogger(__name__)

# ... (Previous imports and helper functions remain same) ...
def clean_html(raw_html):
    if not raw_html: return ""
    try:
        soup = BeautifulSoup(raw_html, "html.parser")
        return soup.get_text(separator=" ").strip()
    except:
        return str(raw_html)

async def push_order_status(bakery_id: str, wc_order_id: str, new_status: str):
    """
    Push local status change back to WooCommerce.
    """
    bakery = await db.bakeries.find_one({"_id": bakery_id})
    if not bakery: return
    
    url = bakery.get("wc_url")
    key = bakery.get("wc_consumer_key")
    secret = bakery.get("wc_consumer_secret")
    
    if not (url and key and secret and wc_order_id):
        return

    # Map Local Status -> WC Status
    # Our status: received, in_production, ready, delivered
    # WC status: processing, completed
    wc_status_slug = "processing" # Default
    
    if new_status == OrderStatus.DELIVERED:
        wc_status_slug = "completed"
    elif new_status == OrderStatus.READY:
        wc_status_slug = "processing" # Or custom status if they have one? Keep processing for now.
        # Maybe add a note?
    elif new_status == OrderStatus.CANCELLED:
        wc_status_slug = "cancelled"
        
    try:
        wcapi = API(url=url, consumer_key=key, consumer_secret=secret, version="wc/v3", timeout=20)
        data = {"status": wc_status_slug}
        
        # If Ready, maybe add a note?
        if new_status == OrderStatus.READY:
            # We don't change status to completed yet, but maybe add note
            wcapi.post(f"orders/{wc_order_id}/notes", {"note": "Il tuo ordine è PRONTO per il ritiro!", "customer_note": True})
            
        response = wcapi.put(f"orders/{wc_order_id}", data)
        if response.status_code == 200:
            logger.info(f"Pushed status {wc_status_slug} to WC Order {wc_order_id}")
        else:
            logger.error(f"Failed to push status to WC: {response.text}")
            
    except Exception as e:
        logger.error(f"Error pushing status to WC: {e}")

async def sync_bakery(bakery):
    # ... (Keep existing sync_bakery logic mostly as is, just ensure parsers are used) ...
    # I am overwriting the file so I must include the full content of sync_bakery here.
    bakery_id = str(bakery["_id"])
    url = bakery.get("wc_url")
    key = bakery.get("wc_consumer_key")
    secret = bakery.get("wc_consumer_secret")
    
    if not (url and key and secret): return

    try:
        wcapi = API(url=url, consumer_key=key, consumer_secret=secret, version="wc/v3", timeout=20)
        
        # --- PRODUCTS ---
        page = 1
        while True:
            r = wcapi.get("products", params={"per_page": 50, "page": page})
            if r.status_code != 200: break
            products = r.json()
            if not products: break
            
            for p in products:
                wc_id = str(p["id"])
                custom_id = f"{bakery_id}_{wc_id}"
                prod_data = {
                    "bakery_id": bakery_id,
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
                await db.products.update_one({"_id": custom_id}, {"$set": prod_data}, upsert=True)
            page += 1

        # --- ORDERS ---
        r = wcapi.get("orders", params={"per_page": 20})
        if r.status_code == 200:
            orders = r.json()
            for o in orders:
                wc_id = str(o["id"])
                custom_id = f"{bakery_id}_{wc_id}"
                existing = await db.orders.find_one({"_id": custom_id})
                
                order_meta = parse_wc_order_meta(o)
                items = []
                for item in o["line_items"]:
                    p_id = f"{bakery_id}_{item['product_id']}"
                    item_meta = parse_wc_item_meta(item)
                    items.append({
                        "wc_item_id": str(item.get("id")),
                        "product_id": p_id,
                        "product_name": item["name"],
                        "quantity": item["quantity"],
                        "unit_price": float(item["price"] or 0),
                        "meta": item_meta
                    })

                status_map = {
                    "processing": OrderStatus.RECEIVED, "pending": OrderStatus.RECEIVED,
                    "completed": OrderStatus.DELIVERED, "cancelled": OrderStatus.CANCELLED,
                    "refunded": OrderStatus.CANCELLED, "failed": OrderStatus.CANCELLED,
                    "on-hold": OrderStatus.RECEIVED
                }
                wc_status = status_map.get(o["status"], OrderStatus.RECEIVED)
                final_status = wc_status
                
                if existing:
                    local = existing.get("status")
                    if local in [OrderStatus.IN_PRODUCTION, OrderStatus.READY] and wc_status == OrderStatus.RECEIVED:
                        final_status = local
                
                payment_status = "unpaid"
                if o["status"] in ["processing", "completed"] or o.get("date_paid"): payment_status = "paid"

                order_data = {
                    "bakery_id": bakery_id, "wc_order_id": wc_id,
                    "customer": {
                        "first_name": o.get("billing", {}).get("first_name", ""),
                        "last_name": o.get("billing", {}).get("last_name", ""),
                        "phone": o.get("billing", {}).get("phone", ""),
                        "email": o.get("billing", {}).get("email", ""),
                    },
                    "customer_name": f"{o['billing']['first_name']} {o['billing']['last_name']}",
                    "customer_email": o["billing"]["email"],
                    "items": items, "total_amount": float(o["total"]),
                    "status": final_status, "payment_status": payment_status,
                    "pickup_date": order_meta["pickup_date"], "pickup_time": order_meta["pickup_time"],
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
            async for bakery in db.bakeries.find({"wc_url": {"$exists": True}}):
                await sync_bakery(bakery)
        except Exception as e:
            logger.error(f"Global Sync Loop Error: {e}")
        await asyncio.sleep(60)
