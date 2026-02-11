import requests

print("--- PRODUCTS API ---")
try:
    r = requests.get("http://localhost:8001/api/inventory/products")
    # Pretty print the first item
    print(r.json()[0]["_id"])
except Exception as e:
    print(e)
