from fastapi import APIRouter, HTTPException, Depends, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import List
from datetime import datetime, timezone
import random
from models import Order, OrderCreate, OrderStatus, OrderItem
from database import get_db # We will create this helper

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
    # Calculate total
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
    result = await db.orders.find_one_and_update(
        {"_id": order_id},
        {"$set": {"status": status, "updated_at": datetime.now(timezone.utc)}},
        return_document=True
    )
    if not result:
        raise HTTPException(status_code=404, detail="Order not found")
    return result

@router.post("/webhook/woocommerce", response_model=Order)
async def woocommerce_webhook(data: dict, db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Simulates receiving an order from WooCommerce.
    Data expected to be loosely shaped like a WC order.
    """
    items = []
    total = 0.0
    
    # Extract items safely
    for item in data.get("line_items", []):
        qty = item.get("quantity", 1)
        price = float(item.get("price", 10.0))
        total += qty * price
        items.append(OrderItem(
            product_id=str(item.get("product_id", "0")),
            product_name=item.get("name", "Unknown Pastry"),
            quantity=qty,
            unit_price=price
        ))

    order = Order(
        customer_name=f"{data.get('billing', {}).get('first_name', 'Guest')} {data.get('billing', {}).get('last_name', '')}",
        customer_email=data.get('billing', {}).get('email', 'no-email@test.com'),
        items=items,
        total_amount=total,
        source="woocommerce"
    )
    
    await db.orders.insert_one(order.model_dump(by_alias=True))
    return order

@router.post("/simulate", response_model=Order)
async def simulate_random_order(db: AsyncIOMotorDatabase = Depends(get_db)):
    """Generates a random order for demo purposes"""
    names = ["Giulia Rossi", "Marco Bianchi", "Sofia Verdi", "Luca Neri"]
    products = [
        ("Torta Sacher", 35.0), ("Croissant Pistacchio", 2.5), 
        ("Bignè Crema", 1.8), ("Cannolo Siciliano", 3.0),
        ("Tiramisu Box", 25.0)
    ]
    
    selected_prods = random.sample(products, k=random.randint(1, 3))
    items = []
    total = 0
    
    for name, price in selected_prods:
        qty = random.randint(1, 5)
        items.append(OrderItem(
            product_id="sim-1",
            product_name=name,
            quantity=qty,
            unit_price=price
        ))
        total += qty * price
        
    order = Order(
        customer_name=random.choice(names),
        customer_email="demo@example.com",
        items=items,
        total_amount=total,
        source="woocommerce_mock"
    )
    
    await db.orders.insert_one(order.model_dump(by_alias=True))
    return order

@router.get("/stats")
async def get_stats(db: AsyncIOMotorDatabase = Depends(get_db)):
    # Simple aggregation
    total_orders = await db.orders.count_documents({})
    pending = await db.orders.count_documents({"status": "received"})
    production = await db.orders.count_documents({"status": "in_production"})
    completed = await db.orders.count_documents({"status": "ready"})
    
    # Revenue today
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
