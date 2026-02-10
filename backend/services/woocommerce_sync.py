import asyncio
import logging
import os
from database import db
from woocommerce import API
from models import Product, Order, OrderItem, OrderStatus
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

def get_wc_api():
    url = os.environ.get("WC_URL")
    key = os.environ.get("WC_CONSUMER_KEY")
    secret = os.environ.get("WC_CONSUMER_SECRET")
    
    if not (url and key and secret):
        return None
        
    return API(
        url=url,
        consumer_key=key,
        consumer_secret=secret,
        version="wc/v3",
        timeout=20
    )

async def sync_products(wcapi):
    try:
        response = wcapi.get("products", params={"per_page": 100})
        if response.status_code != 200:
            logger.error(f"WC Products Sync Failed: {response.text}")
            return
            
        products = response.json()
        count = 0
        for p in products:
            # Check if exists
            existing = await db.products.find_one({"_id": str(p["id"])})
            
            prod_data = {
                "name": p["name"],
                "description": p["short_description"] or p["description"], # HTML stripped ideally
                "price": float(p["price"] or 0),
                "category": p["categories"][0]["name"] if p["categories"] else "General",
                "image_url": p["images"][0]["src"] if p["images"] else None
            }
            
            if existing:
                await db.products.update_one({"_id": str(p["id"])}, {"$set": prod_data})
            else:
                prod_data["_id"] = str(p["id"]) # Use WC ID as DB ID for sync
                await db.products.insert_one(prod_data)
                count += 1
                
        logger.info(f"Synced {len(products)} products. New: {count}")
    except Exception as e:
        logger.error(f"Error syncing products: {e}")

async def sync_orders(wcapi):
    try:
        # Fetch orders modified recently? For MVP just fetch last 20
        response = wcapi.get("orders", params={"per_page": 20})
        if response.status_code != 200:
            logger.error(f"WC Orders Sync Failed: {response.text}")
            return

        orders = response.json()
        count = 0
        for o in orders:
            # We map WC status to our internal status
            # pending, processing, on-hold, completed, cancelled, refunded, failed
            
            # Skip if exists
            existing = await db.orders.find_one({"_id": str(o["id"])})
            if existing:
                # Update status if changed remotely?
                # For now, let's assume local status takes precedence or we only import new ones
                continue

            items = []
            for item in o["line_items"]:
                items.append({
                    "product_id": str(item["product_id"]),
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
            
            new_order = {
                "_id": str(o["id"]),
                "customer_name": f"{o['billing']['first_name']} {o['billing']['last_name']}",
                "customer_email": o["billing"]["email"],
                "source": "woocommerce",
                "items": items,
                "total_amount": float(o["total"]),
                "status": status_map.get(o["status"], OrderStatus.RECEIVED),
                "created_at": datetime.fromisoformat(o["date_created_gmt"]).replace(tzinfo=timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "notes": o.get("customer_note", "")
            }
            
            await db.orders.insert_one(new_order)
            count += 1
            
        if count > 0:
            logger.info(f"Synced {count} new orders from WooCommerce")
            
    except Exception as e:
        logger.error(f"Error syncing orders: {e}")

async def sync_customers(wcapi):
    try:
        response = wcapi.get("customers", params={"per_page": 50})
        if response.status_code != 200:
            return

        customers = response.json()
        for c in customers:
            # Sync to users collection?
            # Or just rely on the aggregation endpoint
            pass
            
    except Exception as e:
        logger.error(f"Error syncing customers: {e}")

async def sync_woocommerce():
    """
    Simulates fetching data from WooCommerce every 60 seconds.
    """
    logger.info("Starting WooCommerce Sync Service...")
    
    while True:
        try:
            wcapi = get_wc_api()
            if wcapi:
                logger.info("Connecting to WooCommerce...")
                await sync_products(wcapi)
                await sync_orders(wcapi)
                await sync_customers(wcapi)
                logger.info("Sync Cycle Completed.")
            else:
                logger.warning("WooCommerce Keys missing. Sync skipped.")
                
        except Exception as e:
            logger.error(f"CRITICAL Sync Error: {e}")
            
        # Wait 60 seconds
        await asyncio.sleep(60)
