import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import json

async def inspect_db_product():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["test_database"]
    
    print("--- DB PRODUCTS ---")
    async for p in db.products.find({}):
        print(f"Name: {p.get('name')}")
        print(f"Price: {p.get('price')} (Type: {type(p.get('price'))})")
        print(f"Image URL: {p.get('image_url')}")
        print(f"Category: {p.get('category')}")
        print(f"Source: {p.get('source')}")
        print("-" * 20)

asyncio.run(inspect_db_product())
