import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import requests
import uuid

async def setup_data():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["test_database"]
    
    # 1. Insert a delivered order (for Chart) with STRING ID
    await db.orders.insert_one({
        "_id": str(uuid.uuid4()),
        "customer_name": "Chart User",
        "customer_email": "chart@test.com",
        "status": "delivered",
        "total_amount": 50.0,
        "items": [],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "source": "manual_test"
    })

asyncio.run(setup_data())

print("Testing Sales History (Today)...")
try:
    r = requests.get("http://localhost:8001/api/orders/sales-history?range=today")
    print(r.status_code)
    print(r.text[:200])
except Exception as e:
    print(e)
