import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient

async def cleanup():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["test_database"]
    
    # Delete orders with missing 'items' field
    res = await db.orders.delete_many({"items": {"$exists": False}})
    print(f"Deleted {res.deleted_count} bad orders (missing items)")

    # Delete orders where _id is NOT a string (i.e. ObjectId)
    # MongoDB query for type 7 (ObjectId)
    res2 = await db.orders.delete_many({"_id": {"$type": 7}})
    print(f"Deleted {res2.deleted_count} bad orders (ObjectId type)")

asyncio.run(cleanup())
