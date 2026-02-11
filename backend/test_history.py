import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

async def test_agg():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["test_database"]
    
    # 1. Create a dummy product
    await db.products.insert_one({"_id": "test-prod-1", "name": "Torta Test"})
    
    # 2. Create a dummy order with that product
    await db.orders.insert_one({
        "customer_name": "History User",
        "customer_email": "hist@test.com",
        "items": [
            {"product_id": "test-prod-1", "product_name": "Torta Test", "quantity": 1, "unit_price": 10}
        ],
        "created_at": datetime.now()
    })
    
    # 3. Run aggregation
    pipeline = [
        {"$unwind": "$items"},
        {"$match": {"items.product_id": "test-prod-1"}},
        {"$project": {
            "customer_name": 1,
            "customer_email": 1,
            "quantity": "$items.quantity",
            "created_at": 1,
            "_id": 0
        }},
        {"$sort": {"created_at": -1}}
    ]
    
    res = await db.orders.aggregate(pipeline).to_list(100)
    print("History Result:", res)
    
    # Cleanup
    await db.products.delete_one({"_id": "test-prod-1"})
    await db.orders.delete_many({"customer_name": "History User"})

asyncio.run(test_agg())
