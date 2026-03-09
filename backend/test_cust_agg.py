import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def test_agg():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["test_database"]
    
    # Pick a bakery ID from the debug output
    bakery_id = "698be51a00ebf958b8d1110e"
    
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
    
    print(f"Running aggregation for bakery: {bakery_id}")
    res = await db.orders.aggregate(pipeline).to_list(100)
    print(f"Result count: {len(res)}")
    for r in res:
        print(r)

asyncio.run(test_agg())
