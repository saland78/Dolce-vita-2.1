from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorDatabase
from database import get_db
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/customers", tags=["customers"])

class CustomerSummary(BaseModel):
    name: str
    email: Optional[str] = None
    total_spent: float
    last_order_date: Optional[str] = None
    source: str = "woocommerce"

@router.get("/", response_model=List[CustomerSummary])
async def get_customers(db: AsyncIOMotorDatabase = Depends(get_db)):
    """
    Aggregates customers from Orders to show a list of people who have purchased.
    In the future, this will sync directly from the 'users' table or WooCommerce Customers API.
    """
    pipeline = [
        {"$group": {
            "_id": "$customer_email",
            "name": {"$first": "$customer_name"},
            "email": {"$first": "$customer_email"},
            "total_spent": {"$sum": "$total_amount"},
            "last_order_date": {"$max": "$created_at"},
            "source": {"$first": "$source"}
        }},
        {"$sort": {"last_order_date": -1}},
        {"$project": {
            "_id": 0,
            "name": 1, 
            "email": 1,
            "total_spent": 1,
            "last_order_date": 1,
            "source": 1
        }}
    ]
    
    customers = await db.orders.aggregate(pipeline).to_list(100)
    
    # Format date for response
    for c in customers:
        if c.get("last_order_date"):
            c["last_order_date"] = c["last_order_date"].isoformat()
            
    return customers
