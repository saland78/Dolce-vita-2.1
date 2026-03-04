import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import requests
import uuid
import datetime

# 1. Simulate Auth & Context
# We can't easily simulate Auth Middleware without a running server accepting cookies.
# But we can simulate the DB insertion logic that the route performs.

async def test_logic():
    from models import Ingredient, IngredientCreate
    
    bakery_id = "test_bakery_123"
    payload = {
        "name": "Test Flour",
        "quantity": 10.0,
        "unit": "kg",
        "reorder_threshold": 5.0,
        "cost_per_unit": 1.5
    }
    
    try:
        ing_in = IngredientCreate(**payload)
        print("IngredientCreate Validation: OK")
    except Exception as e:
        print(f"IngredientCreate Failed: {e}")
        return

    try:
        ing = Ingredient(
            bakery_id=bakery_id,
            **ing_in.model_dump()
        )
        print("Ingredient Construction: OK")
        print(ing.model_dump())
    except Exception as e:
        print(f"Ingredient Construction Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_logic())
