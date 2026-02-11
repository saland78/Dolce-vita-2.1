import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import requests

async def setup_data():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["test_database"]
    
    # 1. Insert a delivered order (for Chart)
    await db.orders.insert_one({
        "customer_name": "Chart User",
        "customer_email": "chart@test.com",
        "status": "delivered",
        "total_amount": 50.0,
        "items": [],
        "created_at": datetime.now(),
        "source": "manual_test"
    })
    
    # 2. Insert a received order (for Production Plan)
    await db.orders.insert_one({
        "customer_name": "Plan User",
        "customer_email": "plan@test.com",
        "status": "received",
        "total_amount": 20.0,
        "items": [
            {"product_name": "Torta Test", "quantity": 2, "product_id": "p1", "unit_price": 10.0}
        ],
        "created_at": datetime.now(),
        "notes": "No gluten",
        "source": "manual_test"
    })

asyncio.run(setup_data())

# Test Endpoints
print("Testing Sales History (Today)...")
r = requests.get("http://localhost:8001/api/orders/sales-history?range=today")
print(r.text)

print("\nTesting Production Plan...")
r = requests.get("http://localhost:8001/api/orders/production-plan")
print(r.text)
