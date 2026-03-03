import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from woocommerce import API
import json

async def debug_wc():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client["test_database"]
    
    # 1. Get Keys from Bakery
    bakery = await db.bakeries.find_one({"wc_url": {"$exists": True}})
    if not bakery:
        print("No bakery with keys found.")
        return

    print(f"Using Bakery: {bakery['name']}")
    url = bakery["wc_url"]
    key = bakery["wc_consumer_key"]
    secret = bakery["wc_consumer_secret"]
    
    # 2. Connect to WC
    wcapi = API(url=url, consumer_key=key, consumer_secret=secret, version="wc/v3", timeout=20)
    
    # 3. Fetch 1 product
    print("Fetching products...")
    response = wcapi.get("products", params={"per_page": 1})
    
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text}")
        return
        
    products = response.json()
    if not products:
        print("No products found.")
        return
        
    p = products[0]
    print("\n--- RAW PRODUCT DATA ---")
    # Print relevant fields only to keep log clean
    debug_data = {
        "id": p.get("id"),
        "name": p.get("name"),
        "type": p.get("type"), # simple vs variable
        "price": p.get("price"),
        "regular_price": p.get("regular_price"),
        "images": p.get("images"),
        "categories": p.get("categories"),
    }
    print(json.dumps(debug_data, indent=2))

asyncio.run(debug_wc())
