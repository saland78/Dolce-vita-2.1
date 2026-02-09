from fastapi import APIRouter, HTTPException, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List
from datetime import datetime, timezone
import random
from models import Order, OrderCreate, OrderStatus, OrderItem
from database import get_db
from services.email_service import EmailService

router = APIRouter(prefix="/orders", tags=["orders"])

@router.get("/", response_model=List[Order])
async def get_orders(status: str = None, db: AsyncIOMotorDatabase = Depends(get_db)):
    query = {}
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
        source="manual"
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

@router.post("/simulate", response_model=Order)
async def simulate_random_order(db: AsyncIOMotorDatabase = Depends(get_db)):
    names = ["Giulia Rossi", "Marco Bianchi", "Sofia Verdi", "Luca Neri"]
    
    # Fetch real products for simulation
    products_docs = await db.products.find({}, {"_id": 1, "name": 1, "price": 1}).to_list(10)
    if not products_docs:
        products_docs = [{"_id": "sim-1", "name": "Torta Sacher", "price": 35.0}] # Fallback
        
    selected_prods = random.sample(products_docs, k=random.randint(1, 3))
    items = []
    total = 0
    
    for prod in selected_prods:
        qty = random.randint(1, 5)
        items.append(OrderItem(
            product_id=str(prod["_id"]),
            product_name=prod["name"],
            quantity=qty,
            unit_price=prod["price"]
        ))
        total += qty * prod["price"]
        
    order = Order(
        customer_name=random.choice(names),
        customer_email="demo.customer@example.com", # Added for email testing
        items=items,
        total_amount=total,
        source="woocommerce_mock"
    )
    
    await db.orders.insert_one(order.model_dump(by_alias=True))
    return order

@router.get("/stats")
async def get_stats(db: AsyncIOMotorDatabase = Depends(get_db)):
    total_orders = await db.orders.count_documents({})
    pending = await db.orders.count_documents({"status": "received"})
    production = await db.orders.count_documents({"status": "in_production"})
    completed = await db.orders.count_documents({"status": "ready"})
    
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    cursor = db.orders.find({"created_at": {"$gte": today_start}})
    today_revenue = 0
    async for doc in cursor:
        today_revenue += doc.get("total_amount", 0)
        
    return {
        "total_orders": total_orders,
        "pending": pending,
        "production": production,
        "completed": completed,
        "today_revenue": today_revenue
    }
