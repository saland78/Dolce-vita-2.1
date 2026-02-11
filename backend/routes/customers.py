from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from database import get_db
from typing import List, Optional
from pydantic import BaseModel
from dependencies import get_current_user_and_bakery

router = APIRouter(prefix="/customers", tags=["customers"])

class CustomerSummary(BaseModel):
    name: str
    email: Optional[str] = None
    total_spent: float
    last_order_date: Optional[str] = None
    orders_count: Optional[int] = 0
    source: str = "woocommerce"

@router.get("/", response_model=List[CustomerSummary])
async def get_customers(
    db: AsyncIOMotorDatabase = Depends(get_db),
    context: tuple = Depends(get_current_user_and_bakery)
):
    _, bakery_id = context
    
    # 1. Fetch synced customers for tenant
    synced_customers = await db.customers.find({"bakery_id": bakery_id}).sort("total_spent", -1).to_list(100)
    if synced_customers:
        return synced_customers

    # Fallback Aggregation
    pipeline = [
        {"$match": {"bakery_id": bakery_id}},
        {"$group": {
            "_id": "$customer_email",
            "name": {"$first": "$customer_name"},
            "email": {"$first": "$customer_email"},
            "total_spent": {"$sum": "$total_amount"},
            "last_order_date": {"$max": "$created_at"},
            "orders_count": {"$sum": 1},
            "source": {"$first": "$source"}
        }},
        {"$sort": {"last_order_date": -1}},
        {"$project": {
            "_id": 0,
            "name": 1, 
            "email": 1,
            "total_spent": 1,
            "last_order_date": 1,
            "orders_count": 1,
            "source": 1
        }}
    ]
    
    customers = await db.orders.aggregate(pipeline).to_list(100)
    
    for c in customers:
        if c.get("last_order_date"):
            c["last_order_date"] = c["last_order_date"].isoformat()
            
    return customers
