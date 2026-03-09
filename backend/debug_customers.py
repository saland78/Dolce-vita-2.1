import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def inspect_customers():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["test_database"]
    
    print("--- CUSTOMERS COLLECTION ---")
    count = await db.customers.count_documents({})
    print(f"Total synced customers: {count}")
    async for c in db.customers.find({}):
        print(c)

    print("\n--- ORDERS COLLECTION (Sample) ---")
    async for o in db.orders.find({}, {"customer_email": 1, "customer_name": 1, "bakery_id": 1}).limit(5):
        print(o)

asyncio.run(inspect_customers())
