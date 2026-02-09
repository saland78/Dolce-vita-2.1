import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

async def test():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["test_database"]
    
    # Insert dummy order
    await db.orders.insert_one({
        "customer_name": "Test User",
        "customer_email": "test@test.com",
        "total_amount": 100.0,
        "created_at": datetime.now(),
        "status": "received",
        "source": "manual"
    })
    
    # Run aggregation
    pipeline = [
        {"$group": {
            "_id": "$customer_email",
            "name": {"$first": "$customer_name"},
            "email": {"$first": "$customer_email"},
            "total_spent": {"$sum": "$total_amount"},
            "last_order_date": {"$max": "$created_at"},
            "source": {"$first": "$source"}
        }}
    ]
    res = await db.orders.aggregate(pipeline).to_list(100)
    print("Aggregation Result:", res)

asyncio.run(test())
