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
    print("Testing connection...")
    try:
        response = wcapi.get("products", params={"per_page": 1})
        print(f"Status: {response.status_code}")
        print(f"Body: {response.text[:500]}")
    except Exception as e:
        print(f"Error: {e}")

test_conn()
