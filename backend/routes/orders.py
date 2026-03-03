from fastapi import APIRouter, HTTPException, Depends, Query, Response
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
from models import Order, OrderCreate, OrderStatus
from database import get_db
from services.email_service import EmailService
from services.woocommerce_sync import push_order_status
from services.pdf_service import generate_production_sheet_pdf
from dependencies import get_current_user_and_bakery

router = APIRouter(prefix="/orders", tags=["orders"])

class ProductionStatusUpdate(BaseModel):
    product_id: str
    completed: bool
    date: str

# ... (get_orders, create_order remain same) ...
@router.get("/", response_model=List[Order])
async def get_orders(
    status: str = None, 
    archived: bool = False, 
    db: AsyncIOMotorDatabase = Depends(get_db),
    context: tuple = Depends(get_current_user_and_bakery)
):
    _, bakery_id = context
    query = {"bakery_id": bakery_id}
    if not archived: query["archived"] = {"$ne": True}
    else: query["archived"] = True
    if status: query["status"] = status
    orders = await db.orders.find(query).sort("created_at", -1).to_list(100)
    return orders

@router.put("/{order_id}/status", response_model=Order)
async def update_status(
    order_id: str, 
    status: OrderStatus, 
    db: AsyncIOMotorDatabase = Depends(get_db),
    context: tuple = Depends(get_current_user_and_bakery)
):
    _, bakery_id = context
    
    original_order = await db.orders.find_one({"_id": order_id, "bakery_id": bakery_id})
    if not original_order:
        raise HTTPException(status_code=404, detail="Order not found")

    result = await db.orders.find_one_and_update(
        {"_id": order_id, "bakery_id": bakery_id},
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc)}},
        return_document=True
    )

    # 1. Email Trigger
    if status == OrderStatus.READY and original_order.get("status") != OrderStatus.READY:
        customer_email = result.get("customer_email")
        if customer_email:
            await EmailService.send_order_ready_email(
                to_email=customer_email, 
                customer_name=result.get("customer_name"), 
                order_id=order_id
            )
            
    # 2. WooCommerce Push Trigger (NEW)
    if result.get("wc_order_id"):
        await push_order_status(bakery_id, result.get("wc_order_id"), status)

    return result

@router.get("/{order_id}/production-sheet")
async def get_production_sheet(
    order_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
    context: tuple = Depends(get_current_user_and_bakery)
):
    _, bakery_id = context
    order = await db.orders.find_one({"_id": order_id, "bakery_id": bakery_id})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
        
    pdf_buffer = generate_production_sheet_pdf(order)
    
    return Response(
        content=pdf_buffer.read(),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=scheda_{order_id}.pdf"}
    )

# ... (archive_order, stats, sales-history remain same) ...
@router.put("/{order_id}/archive", response_model=Order)
async def archive_order(
    order_id: str, 
    db: AsyncIOMotorDatabase = Depends(get_db),
    context: tuple = Depends(get_current_user_and_bakery)
):
    _, bakery_id = context
    result = await db.orders.find_one_and_update(
        {"_id": order_id, "bakery_id": bakery_id},
        {"$set": {"archived": True}},
        return_document=True
    )
    if not result:
        raise HTTPException(status_code=404, detail="Order not found")
    return result

@router.get("/stats")
async def get_stats(
    db: AsyncIOMotorDatabase = Depends(get_db),
    context: tuple = Depends(get_current_user_and_bakery)
):
    _, bakery_id = context
    base_query = {"bakery_id": bakery_id, "archived": {"$ne": True}}
    
    total_orders = await db.orders.count_documents(base_query)
    pending = await db.orders.count_documents({**base_query, "status": "received"})
    production = await db.orders.count_documents({**base_query, "status": "in_production"})
    completed = await db.orders.count_documents({**base_query, "status": "ready"})
    
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    pipeline = [
        {
            "$match": {
                "bakery_id": bakery_id,
                "created_at": {"$gte": today_start},
                "status": {"$ne": OrderStatus.CANCELLED},
                "archived": {"$ne": True}
            }
        },
        {
            "$group": {
                "_id": None,
                "total": {"$sum": "$total_amount"}
            }
        }
    ]
    
    agg = await db.orders.aggregate(pipeline).to_list(1)
    today_revenue = agg[0]["total"] if agg else 0
        
    return {
        "total_orders": total_orders,
        "pending": pending,
        "production": production,
        "completed": completed,
        "today_revenue": today_revenue
    }

@router.get("/sales-history")
async def get_sales_history(
    time_range: str = Query("7d", alias="range"), 
    db: AsyncIOMotorDatabase = Depends(get_db),
    context: tuple = Depends(get_current_user_and_bakery)
):
    _, bakery_id = context
    now = datetime.now(timezone.utc)
    
    if time_range == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        group_format = {"hour": {"$hour": "$created_at"}}
    else:
        start_date = now - timedelta(days=7)
        group_format = {"year": {"$year": "$created_at"}, "month": {"$month": "$created_at"}, "day": {"$dayOfMonth": "$created_at"}}
        
        if time_range == "7d": start_date = now - timedelta(days=7)
        elif time_range == "30d": start_date = now - timedelta(days=30)
        elif time_range == "6m":
            start_date = now - timedelta(days=180)
            group_format = {"year": {"$year": "$created_at"}, "month": {"$month": "$created_at"}}
        elif time_range == "1y":
            start_date = now - timedelta(days=365)
            group_format = {"year": {"$year": "$created_at"}, "month": {"$month": "$created_at"}}

    pipeline = [
        {
            "$match": {
                "bakery_id": bakery_id,
                "created_at": {"$gte": start_date},
                "status": {"$ne": OrderStatus.CANCELLED}
            }
        },
        {"$group": {
            "_id": group_format,
            "sales": {"$sum": "$total_amount"}
        }},
        {"$sort": {"_id.year": 1, "_id.month": 1, "_id.day": 1, "_id.hour": 1}}
    ]
    
    data = await db.orders.aggregate(pipeline).to_list(1000)
    
    formatted = []
    sales_map = {}
    
    for d in data:
        key = ""
        label = ""
        if "hour" in d["_id"]:
            key = str(d["_id"]["hour"])
            label = f"{d['_id']['hour']}:00"
        elif "day" in d["_id"]:
            key = f"{d['_id']['day']}/{d['_id']['month']}"
            label = key
        else:
            key = f"{d['_id']['month']}/{d['_id']['year']}"
            label = key
        
        sales_map[key] = d['sales']
        if time_range != "today":
             formatted.append({"name": label, "sales": d['sales']})

    if time_range == "today":
        for h in range(24):
            key = str(h)
            formatted.append({"name": f"{h}:00", "sales": sales_map.get(str(h), 0)})
            
    return formatted

# --- PRODUCTION PLAN (SLOTS VIEW) ---
# NOTE: The user requested a "Production Plan" view that groups by pickup slot.
# I am updating the endpoint to return full details, not just aggregated items.
# Or better, create a new endpoint /orders/daily-slots

@router.get("/daily-slots")
async def get_daily_slots(
    db: AsyncIOMotorDatabase = Depends(get_db),
    context: tuple = Depends(get_current_user_and_bakery)
):
    _, bakery_id = context
    
    # Fetch active orders
    orders = await db.orders.find({
        "bakery_id": bakery_id,
        "archived": {"$ne": True},
        "status": {"$in": ["received", "in_production", "ready"]}
    }).sort("pickup_time", 1).to_list(1000)
    
    # Group in Python because Mongo Grouping is complex for this specific UI structure
    grouped = {} # { "YYYY-MM-DD": { "HH:MM": [order1, order2] } }
    
    for o in orders:
        p_date = o.get("pickup_date") or "Data non specificata"
        p_time = o.get("pickup_time") or "Orario n/d"
        
        if p_date not in grouped: grouped[p_date] = {}
        if p_time not in grouped[p_date]: grouped[p_date][p_time] = []
        
        grouped[p_date][p_time].append(o)
        
    return grouped

# Keeping legacy aggregated plan for "Item Totals" view if needed
@router.get("/production-plan")
async def get_production_plan(
    date: Optional[str] = None, 
    db: AsyncIOMotorDatabase = Depends(get_db),
    context: tuple = Depends(get_current_user_and_bakery)
):
    _, bakery_id = context
    target_date = date or datetime.now().strftime("%Y-%m-%d")
    
    pipeline = [
        {
            "$match": {
                "bakery_id": bakery_id,
                "status": {"$in": ["received", "in_production"]},
                "archived": {"$ne": True}
            }
        },
        {"$unwind": "$items"},
        {"$group": {
            "_id": "$items.product_id", 
            "original_name": {"$first": "$items.product_name"},
            "total_quantity": {"$sum": "$items.quantity"},
            "orders": {"$push": {
                "customer": "$customer_name",
                "qty": "$items.quantity",
                "notes": "$notes"
            }}
        }},
        {"$lookup": {
            "from": "products",
            "localField": "_id",
            "foreignField": "_id",
            "as": "product_info"
        }},
        {"$unwind": {"path": "$product_info", "preserveNullAndEmptyArrays": True}},
        {"$project": {
            "product_name": {"$ifNull": ["$product_info.name", "$original_name"]},
            "image_url": "$product_info.image_url",
            "total_quantity": 1,
            "orders": 1
        }},
        {"$sort": {"total_quantity": -1}}
    ]
    
    plan = await db.orders.aggregate(pipeline).to_list(100)
    
    statuses = await db.production_status.find({
        "bakery_id": bakery_id,
        "date": target_date
    }).to_list(1000)
    status_map = {s["product_id"]: s["completed"] for s in statuses}
    
    for item in plan:
        item["completed"] = status_map.get(item["_id"], False)
        
    return plan

@router.post("/production-plan/toggle")
async def toggle_production_status(
    update: ProductionStatusUpdate, 
    db: AsyncIOMotorDatabase = Depends(get_db),
    context: tuple = Depends(get_current_user_and_bakery)
):
    _, bakery_id = context
    await db.production_status.update_one(
        {"bakery_id": bakery_id, "date": update.date, "product_id": update.product_id},
        {"$set": {"completed": update.completed, "updated_at": datetime.now(timezone.utc)}},
        upsert=True
    )
    return {"status": "ok"}
