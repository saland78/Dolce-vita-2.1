import asyncio
from woocommerce import API
import os

URL="https://pasticceria.andreasalardi.it/"
KEY="ck_ab867c18e0d0f51ae9866e7f334bed10438f792a"
SECRET="cs_d78367417badb039c6201d74f76ab55920800fe5"

def test_conn():
    wcapi = API(
        url=URL,
        consumer_key=KEY,
        consumer_secret=SECRET,
        version="wc/v3",
        timeout=20
    )
    print("--- PRODUCTS ---")
    res_p = wcapi.get("products", params={"status": "any"}) # Get drafts too
    print(f"Count: {len(res_p.json())}")
    print(res_p.text[:300])

    print("\n--- ORDERS ---")
    res_o = wcapi.get("orders")
    print(f"Count: {len(res_o.json())}")
    
test_conn()
