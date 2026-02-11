import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def cleanup():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["test_database"]
    await db.orders.delete_many({"source": "manual_test"})

asyncio.run(cleanup())
