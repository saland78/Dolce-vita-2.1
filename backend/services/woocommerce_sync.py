import asyncio
import logging
import os
import re
from database import db
from woocommerce import API
from models import Product, Order, OrderStatus
from datetime import datetime, timezone
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

def clean_html(raw_html):
    if not raw_html:
        return ""
    try:
        soup = BeautifulSoup(raw_html, "html.parser")
        text = soup.get_text(separator=" ")
        return text.strip()
    except:
        return re.sub(r'<[^>]+>', '', str(raw_html)).strip()

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
        page = 1
        while True:
            response = wcapi.get("products", params={"per_page": 100, "page": page})
            if response.status_code != 200:
                logger.error(f"WC Products Sync Failed: {response.text}")
                break
                
            products = response.json()
            if not products:
                break
                
            for p in products:
                wc_id = str(p["id"])
                description = clean_html(p["short_description"] or p["description"])
                
                prod_data = {
                    "name": p["name"],
                    "description": description,
                    "price": float(p["price"] or 0),
                    "category": p["categories"][0]["name"] if p["categories"] else "General",
                    "image_url": p["images"][0]["src"] if p["images"] else None,
                    "sku": p.get("sku"),
                    "stock_status": p.get("stock_status"),
                    "source": "woocommerce",
                    "updated_at": datetime.now(timezone.utc)
                }
                
                await db.products.update_one(
                    {"_id": wc_id},
                    {"$set": prod_data},
                    upsert=True
                )
            
            logger.info(f"Synced page {page} of products ({len(products)} items)")
            page += 1
            
    except Exception as e:
        logger.error(f"Error syncing products: {e}")

async def sync_orders(wcapi):
    try:
        response = wcapi.get("orders", params={"per_page": 50})
        if response.status_code != 200:
            logger.error(f"WC Orders Sync Failed: {response.text}")
            return

        orders = response.json()
        count = 0
        for o in orders:
            wc_id = str(o["id"])
            
            existing_order = await db.orders.find_one({"_id": wc_id})
            
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
                "on-hold": OrderStatus.RECEIVED,
                "completed": OrderStatus.DELIVERED,
                "cancelled": OrderStatus.CANCELLED,
                "refunded": OrderStatus.CANCELLED,
                "failed": OrderStatus.CANCELLED
            }
            
            wc_status_mapped = status_map.get(o["status"], OrderStatus.RECEIVED)
            final_status = wc_status_mapped

            if existing_order:
                local_status = existing_order.get("status")
                if local_status in [OrderStatus.IN_PRODUCTION, OrderStatus.READY] and wc_status_mapped == OrderStatus.RECEIVED:
                    final_status = local_status
            
            payment_status = "unpaid"
            if o["status"] in ["processing", "completed"] or o.get("date_paid"):
                payment_status = "paid"

            order_data = {
                "customer_name": f"{o['billing']['first_name']} {o['billing']['last_name']}",
                "customer_email": o["billing"]["email"],
                "source": "woocommerce",
                "items": items,
                "total_amount": float(o["total"]),
                "status": final_status,
                "payment_status": payment_status,
                "created_at": datetime.fromisoformat(o["date_created_gmt"]).replace(tzinfo=timezone.utc),
                "updated_at": datetime.now(timezone.utc),
                "notes": clean_html(o.get("customer_note", ""))
            }
            
            # Ensure archived defaults to False on insert
            if not existing_order:
                order_data["archived"] = False
            
            await db.orders.update_one(
                {"_id": wc_id},
                {"$set": order_data},
                upsert=True
            )
            count += 1
            
        if count > 0:
            logger.info(f"Synced {count} orders from WooCommerce")
            
    except Exception as e:
        logger.error(f"Error syncing orders: {e}")

async def sync_customers(wcapi):
    try:
        response = wcapi.get("customers", params={"per_page": 50})
        if response.status_code != 200:
            return

        customers = response.json()
        for c in customers:
            wc_id = str(c["id"])
            cust_data = {
                "name": f"{c['first_name']} {c['last_name']}".strip() or c['username'],
                "email": c['email'],
                "total_spent": float(c.get('total_spent', 0)),
                "orders_count": c.get('orders_count', 0),
                "last_order_date": c.get('date_last_active_gmt'),
                "source": "woocommerce",
                "avatar_url": c.get('avatar_url'),
                "updated_at": datetime.now(timezone.utc)
            }
            await db.customers.update_one({"_id": wc_id}, {"$set": cust_data}, upsert=True)
            
    except Exception as e:
        logger.error(f"Error syncing customers: {e}")

async def sync_woocommerce():
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
        await asyncio.sleep(60)
