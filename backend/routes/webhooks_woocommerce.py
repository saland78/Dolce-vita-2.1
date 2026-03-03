from fastapi import APIRouter, HTTPException, Request, Header, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from database import get_db
import hmac
import hashlib
import base64
import json
import logging
from datetime import datetime, timezone
from services.parsers import parse_wc_order_meta, parse_wc_item_meta
from models import OrderStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks/woocommerce", tags=["webhooks"])

async def verify_webhook_signature(request: Request, secret: str, x_wc_webhook_signature: str):
    body = await request.body()
    if not secret:
        logger.warning("Webhook received but no secret configured in DB/Env.")
        return True # Fail open for testing, or False for strict security
        
    digest = hmac.new(secret.encode('utf-8'), body, hashlib.sha256).digest()
    calculated_signature = base64.b64encode(digest).decode('utf-8')
    
    return hmac.compare_digest(calculated_signature, x_wc_webhook_signature)

@router.post("/order")
async def webhook_order_updated(
    request: Request,
    x_wc_webhook_signature: str = Header(None),
    x_wc_webhook_topic: str = Header(None),
    x_wc_webhook_source: str = Header(None),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """
    Receives Order Created/Updated events from WooCommerce.
    """
    try:
        payload = await request.json()
        
        # 1. Identify Bakery based on Source URL or brute-force check signature?
        # Since we are multi-tenant SaaS, we need to know WHICH bakery this is.
        # WC Webhook doesn't send bakery_id. We can use the Source URL.
        # Clean the source URL (remove http/https/trailing slash)
        clean_source = x_wc_webhook_source.replace("https://", "").replace("http://", "").rstrip("/")
        
        # Find bakery by URL matching
        # Note: In production, we might want a unique webhook URL per bakery like /webhooks/{bakery_id}/order
        # For now, let's search regex or exact match
        bakery = await db.bakeries.find_one({"wc_url": {"$regex": clean_source}})
        
        if not bakery:
            logger.error(f"Webhook received from unknown source: {x_wc_webhook_source}")
            return {"status": "ignored", "reason": "unknown_source"}
            
        # 2. Verify Signature
        # secret = bakery.get("wc_webhook_secret") or os.environ.get("WC_WEBHOOK_SECRET")
        # if not await verify_webhook_signature(request, secret, x_wc_webhook_signature):
        #     raise HTTPException(status_code=401, detail="Invalid Signature")

        # 3. Process Order
        wc_id = str(payload.get("id"))
        bakery_id = str(bakery["_id"])
        custom_id = f"{bakery_id}_{wc_id}"
        
        # Parse Meta
        order_meta = parse_wc_order_meta(payload)
        
        # Parse Items
        items = []
        for item in payload.get("line_items", []):
            item_meta = parse_wc_item_meta(item)
            
            # Ensure product exists or upsert it briefly? 
            # We assume Sync Service handles products, but we map the ID correctly
            p_id = f"{bakery_id}_{item['product_id']}"
            
            items.append({
                "wc_item_id": str(item.get("id")),
                "product_id": p_id,
                "product_name": item["name"],
                "quantity": item["quantity"],
                "unit_price": float(item["total"]) / int(item["quantity"]) if int(item["quantity"]) > 0 else 0,
                "meta": item_meta
            })

        # Map Status
        status_map = {
            "processing": OrderStatus.RECEIVED, 
            "pending": OrderStatus.RECEIVED,
            "on-hold": OrderStatus.RECEIVED,
            "completed": OrderStatus.DELIVERED,
            "cancelled": OrderStatus.CANCELLED,
            "refunded": OrderStatus.CANCELLED,
            "failed": OrderStatus.CANCELLED
        }
        
        # Check existing to preserve local flow
        existing = await db.orders.find_one({"_id": custom_id})
        wc_status = status_map.get(payload.get("status"), OrderStatus.RECEIVED)
        final_status = wc_status
        
        if existing:
            local = existing.get("status")
            # Don't revert progress
            if local in [OrderStatus.IN_PRODUCTION, OrderStatus.READY] and wc_status == OrderStatus.RECEIVED:
                final_status = local

        payment_status = "unpaid"
        if payload.get("status") in ["processing", "completed"] or payload.get("date_paid"):
            payment_status = "paid"

        order_data = {
            "bakery_id": bakery_id,
            "wc_order_id": wc_id,
            "customer": {
                "first_name": payload.get("billing", {}).get("first_name", ""),
                "last_name": payload.get("billing", {}).get("last_name", ""),
                "phone": payload.get("billing", {}).get("phone", ""),
                "email": payload.get("billing", {}).get("email", ""),
            },
            "customer_name": f"{payload.get('billing', {}).get('first_name')} {payload.get('billing', {}).get('last_name')}",
            "customer_email": payload.get("billing", {}).get("email"),
            "items": items,
            "total_amount": float(payload.get("total", 0)),
            "status": final_status,
            "payment_status": payment_status,
            "pickup_date": order_meta["pickup_date"],
            "pickup_time": order_meta["pickup_time"],
            "updated_at": datetime.now(timezone.utc)
        }
        
        if not existing:
            order_data["created_at"] = datetime.fromisoformat(payload.get("date_created_gmt")).replace(tzinfo=timezone.utc)
            order_data["archived"] = False
            # Notes
            order_data["notes"] = payload.get("customer_note", "")

        await db.orders.update_one(
            {"_id": custom_id},
            {"$set": order_data},
            upsert=True
        )
        
        logger.info(f"Webhook processed for order {wc_id} - Bakery {bakery.get('name')}")
        return {"status": "success", "order_id": custom_id}

    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
