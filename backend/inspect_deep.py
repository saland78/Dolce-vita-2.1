import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def inspect_deep():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["test_database"]
    
    print("--- ALL PRODUCTS ---")
    async for p in db.products.find({}):
        print(f"ID: {p['_id']}")
        print(f"BakeryID: {p.get('bakery_id')}")
        print(f"Name: {p.get('name')}")
        print(f"Price: {p.get('price')}")
        print("-" * 10)

asyncio.run(inspect_deep())
