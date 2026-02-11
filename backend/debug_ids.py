import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def inspect_db():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["test_database"]
    
    print("--- PRODUCTS (First 3) ---")
    async for p in db.products.find({}, {"_id": 1, "name": 1}).limit(3):
        print(p)
        
    print("\n--- ORDERS (First 3) ---")
    async for o in db.orders.find({}, {"items": 1}).limit(3):
        for item in o.get("items", []):
            print(f"Item: {item.get('product_name')} | ID: {item.get('product_id')}")

asyncio.run(inspect_db())
