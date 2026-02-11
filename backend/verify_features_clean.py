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
    
    # 2. Insert a received order (for Production Plan) with STRING ID
    await db.orders.insert_one({
        "_id": str(uuid.uuid4()),
        "customer_name": "Plan User",
        "customer_email": "plan@test.com",
        "status": "received",
        "total_amount": 20.0,
        "items": [
            {"product_name": "Torta Test", "quantity": 2, "product_id": "p1", "unit_price": 10.0}
        ],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
        "notes": "No gluten",
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
