import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import requests

async def deep_inspect():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["test_database"]
    
    print("--- TYPE CHECK ---")
    async for o in db.orders.find({"items.product_name": "Torta di mele della nonna"}):
        for item in o["items"]:
            if item["product_name"] == "Torta di mele della nonna":
                pid = item["product_id"]
                print(f"DB Value: {repr(pid)} | Type: {type(pid)}")

asyncio.run(deep_inspect())

print("\n--- API TEST ---")
try:
    r = requests.get("http://localhost:8001/api/inventory/products/15/orders")
    print(f"Status: {r.status_code}")
    print(f"Response: {r.text}")
except Exception as e:
    print(e)
