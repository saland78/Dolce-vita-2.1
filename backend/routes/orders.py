from fastapi import APIRouter, HTTPException, Depends, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from models import Order, OrderCreate, OrderStatus, OrderItem
from database import get_db
from services.email_service import EmailService

router = APIRouter(prefix="/orders", tags=["orders"])

@router.get("/", response_model=List[Order])
async def get_orders(
    status: str = None, 
    archived: bool = False, # Default to showing active orders only
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    query = {"archived": archived}
    if status:
        query["status"] = status
    orders = await db.orders.find(query).sort("created_at", -1).to_list(100)
    return orders

@router.post("/", response_model=Order)
async def create_order(order_in: OrderCreate, db: AsyncIOMotorDatabase = Depends(get_db)):
    total = sum(item.quantity * item.unit_price for item in order_in.items)
    
    order = Order(
        customer_name=order_in.customer_name,
        customer_email=order_in.customer_email,
        items=order_in.items,
        total_amount=total,
        notes=order_in.notes,
        source="manual",
        status=OrderStatus.RECEIVED
    )
    
    await db.orders.insert_one(order.model_dump(by_alias=True))
    return order

@router.put("/{order_id}/status", response_model=Order)
async def update_status(order_id: str, status: OrderStatus, db: AsyncIOMotorDatabase = Depends(get_db)):
    original_order = await db.orders.find_one({"_id": order_id})
    if not original_order:
        raise HTTPException(status_code=404, detail="Order not found")

    result = await db.orders.find_one_and_update(
        {"_id": order_id},
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc)}},
        return_document=True
    )

    # EMAIL TRIGGER
    if status == OrderStatus.READY and original_order.get("status") != OrderStatus.READY:
        customer_email = result.get("customer_email")
        if customer_email:
            await EmailService.send_order_ready_email(
                to_email=customer_email, 
                customer_name=result.get("customer_name"), 
                order_id=order_id
            )

    return result

@router.put("/{order_id}/archive", response_model=Order)
async def archive_order(order_id: str, db: AsyncIOMotorDatabase = Depends(get_db)):
    result = await db.orders.find_one_and_update(
        {"_id": order_id},
        {"$set": {"archived": True}},
        return_document=True
    )
    if not result:
        raise HTTPException(status_code=404, detail="Order not found")
    return result

@router.get("/stats")
async def get_stats(db: AsyncIOMotorDatabase = Depends(get_db)):
    total_orders = await db.orders.count_documents({})
    pending = await db.orders.count_documents({"status": "received"})
    production = await db.orders.count_documents({"status": "in_production"})
    completed = await db.orders.count_documents({"status": "ready"})
    
    # REVENUE FIX: Sum of all NON-CANCELLED orders created today
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    
    pipeline = [
        {
            "$match": {
                "created_at": {"$gte": today_start},
                "status": {"$ne": OrderStatus.CANCELLED}
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
async def get_sales_history(time_range: str = Query("7d", alias="range"), db: AsyncIOMotorDatabase = Depends(get_db)):
    now = datetime.now(timezone.utc)
    
    if time_range == "today":
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        group_format = {"hour": {"$hour": "$created_at"}}
    elif time_range == "7d":
        start_date = now - timedelta(days=7)
        group_format = {"year": {"$year": "$created_at"}, "month": {"$month": "$created_at"}, "day": {"$dayOfMonth": "$created_at"}}
    elif time_range == "30d":
        start_date = now - timedelta(days=30)
        group_format = {"year": {"$year": "$created_at"}, "month": {"$month": "$created_at"}, "day": {"$dayOfMonth": "$created_at"}}
    elif time_range == "6m":
        start_date = now - timedelta(days=180)
        group_format = {"year": {"$year": "$created_at"}, "month": {"$month": "$created_at"}}
    elif time_range == "1y":
        start_date = now - timedelta(days=365)
        group_format = {"year": {"$year": "$created_at"}, "month": {"$month": "$created_at"}}
    else:
        start_date = now - timedelta(days=7)
        group_format = {"year": {"$year": "$created_at"}, "month": {"$month": "$created_at"}, "day": {"$dayOfMonth": "$created_at"}}

    pipeline = [
        {
            "$match": {
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
            formatted.append({
                "name": f"{h}:00",
                "sales": sales_map.get(key, 0)
            })
            
    return formatted

@router.get("/production-plan")
async def get_production_plan(date: Optional[str] = None, db: AsyncIOMotorDatabase = Depends(get_db)):
    pipeline = [
        {"$match": {"status": {"$in": ["received", "in_production"]}}},
        {"$unwind": "$items"},
        {"$group": {
            "_id": "$items.product_name",
            "total_quantity": {"$sum": "$items.quantity"},
            "orders": {"$push": {
                "customer": "$customer_name",
                "qty": "$items.quantity",
                "notes": "$notes"
            }}
        }},
        {"$sort": {"total_quantity": -1}}
    ]
    
    plan = await db.orders.aggregate(pipeline).to_list(100)
    return plan
