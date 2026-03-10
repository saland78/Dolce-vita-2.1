from fastapi import APIRouter, HTTPException, Depends, Query, Response
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from pydantic import BaseModel
from models import Order, OrderCreate, OrderStatus, OrderItem
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

# ... (Previous Order Routes) ...
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

    old_status = original_order.get("status")

    result = await db.orders.find_one_and_update(
        {"_id": order_id, "bakery_id": bakery_id},
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc)}},
        return_document=True
    )

    customer_email = result.get("customer_email")
    customer_name = result.get("customer_name", "Cliente")

    # Email: ordine pronto
    if status == OrderStatus.READY and old_status != OrderStatus.READY:
        if customer_email:
            await EmailService.send_order_ready(
                db=db, bakery_id=bakery_id,
                to_email=customer_email,
                customer_name=customer_name,
                order_id=order_id
            )

    # Decremento magazzino: quando ordine diventa DELIVERED
    if status == OrderStatus.DELIVERED and old_status != OrderStatus.DELIVERED:
        await _decrement_inventory(db, bakery_id, result)

    if result.get("wc_order_id"):
        await push_order_status(bakery_id, result.get("wc_order_id"), status)

    return result


async def _decrement_inventory(db, bakery_id: str, order: dict):
    """Scala le materie prime dal magazzino in base agli ingredienti delle ricette."""
    items = order.get("items", [])
    if not items:
        return
    # Carica tutte le ricette della bakery
    recipes = {}
    async for r in db.recipes.find({"bakery_id": bakery_id}):
        recipes[r["product_id"]] = r

    for item in items:
        pid = item.get("product_id")
        qty = item.get("quantity", 0)
        recipe = recipes.get(pid)
        if not recipe:
            continue

        base_weight = recipe.get("base_weight_kg", 1.0)
        item_weight = item.get("meta", {}).get("weight_kg")
        scale = (item_weight * qty) / base_weight if item_weight else float(qty)

        for ing in recipe.get("ingredients", []):
            name = ing["name"]
            unit = ing["unit"]
            qty_used = ing["quantity_per_unit"] * scale

            # Converti in kg/litri se necessario per uniformità
            if unit == "gr":
                qty_used_kg = qty_used / 1000
                await db.ingredients.update_one(
                    {"bakery_id": bakery_id, "name": name, "unit": "kg"},
                    {"$inc": {"quantity": -qty_used_kg}}
                )
                await db.ingredients.update_one(
                    {"bakery_id": bakery_id, "name": name, "unit": "gr"},
                    {"$inc": {"quantity": -qty_used}}
                )
            elif unit == "kg":
                await db.ingredients.update_one(
                    {"bakery_id": bakery_id, "name": name, "unit": "kg"},
                    {"$inc": {"quantity": -qty_used}}
                )
                await db.ingredients.update_one(
                    {"bakery_id": bakery_id, "name": name, "unit": "gr"},
                    {"$inc": {"quantity": -(qty_used * 1000)}}
                )
            else:
                await db.ingredients.update_one(
                    {"bakery_id": bakery_id, "name": name, "unit": unit},
                    {"$inc": {"quantity": -qty_used}}
                )

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

# --- PRODUCTION PLAN & SLOTS ---

@router.get("/daily-slots")
async def get_daily_slots(
    db: AsyncIOMotorDatabase = Depends(get_db),
    context: tuple = Depends(get_current_user_and_bakery)
):
    _, bakery_id = context
    
    orders = await db.orders.find({
        "bakery_id": bakery_id,
        "archived": {"$ne": True},
        "status": {"$in": ["received", "in_production", "ready"]}
    }).sort("pickup_time", 1).to_list(1000)
    
    grouped = {} 
    
    for o in orders:
        p_date = o.get("pickup_date") or "Data non specificata"
        p_time = o.get("pickup_time") or "Orario n/d"
        
        if p_date not in grouped: grouped[p_date] = {}
        if p_time not in grouped[p_date]: grouped[p_date][p_time] = []
        
        grouped[p_date][p_time].append(o)
        
    return grouped

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

# --- MANUAL ORDER CREATE FIX ---
@router.post("/", response_model=Order)
async def create_order(
    order_in: OrderCreate, 
    db: AsyncIOMotorDatabase = Depends(get_db),
    context: tuple = Depends(get_current_user_and_bakery)
):
    _, bakery_id = context
    total = sum(item.quantity * item.unit_price for item in order_in.items)
    
    order = Order(
        bakery_id=bakery_id, 
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


@router.get("/sales-report")
async def get_sales_report(
    period: str = "30d",
    db: AsyncIOMotorDatabase = Depends(get_db),
    context: tuple = Depends(get_current_user_and_bakery)
):
    """Report vendite: prodotti più venduti, fatturato per giorno, ordini per stato."""
    _, bakery_id = context
    from datetime import timedelta

    days = {"7d": 7, "30d": 30, "90d": 90, "365d": 365}.get(period, 30)
    since = datetime.now(timezone.utc) - timedelta(days=days)

    pipeline_revenue = [
        {"$match": {
            "bakery_id": bakery_id,
            "status": {"$ne": "cancelled"},
            "created_at": {"$gte": since}
        }},
        {"$group": {
            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$created_at"}},
            "revenue": {"$sum": "$total_amount"},
            "orders": {"$sum": 1}
        }},
        {"$sort": {"_id": 1}}
    ]

    pipeline_products = [
        {"$match": {
            "bakery_id": bakery_id,
            "status": {"$ne": "cancelled"},
            "created_at": {"$gte": since}
        }},
        {"$unwind": "$items"},
        {"$group": {
            "_id": "$items.product_name",
            "total_qty": {"$sum": "$items.quantity"},
            "total_revenue": {"$sum": {"$multiply": ["$items.quantity", {"$ifNull": ["$items.price", 0]}]}}
        }},
        {"$sort": {"total_qty": -1}},
        {"$limit": 10}
    ]

    pipeline_status = [
        {"$match": {"bakery_id": bakery_id, "created_at": {"$gte": since}}},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]

    revenue_by_day = await db.orders.aggregate(pipeline_revenue).to_list(400)
    top_products = await db.orders.aggregate(pipeline_products).to_list(10)
    by_status = await db.orders.aggregate(pipeline_status).to_list(10)

    total_revenue = sum(d["revenue"] for d in revenue_by_day)
    total_orders = sum(d["orders"] for d in revenue_by_day)

    return {
        "period": period,
        "total_revenue": round(total_revenue, 2),
        "total_orders": total_orders,
        "revenue_by_day": [{"date": d["_id"], "revenue": round(d["revenue"], 2), "orders": d["orders"]} for d in revenue_by_day],
        "top_products": [{"name": p["_id"], "qty": p["total_qty"], "revenue": round(p["total_revenue"], 2)} for p in top_products],
        "by_status": {s["_id"]: s["count"] for s in by_status}
    }
