import requests

print("--- PRODUCTS API ---")
try:
    r = requests.get("http://localhost:8001/api/inventory/products")
    products = r.json()
    for p in products:
        print(f"Name: {p.get('name')}")
        print(f"Price: {p.get('price')}")
        print(f"Image: {p.get('image_url')}")
        print(f"Cat: {p.get('category')}")
except Exception as e:
    print(e)
