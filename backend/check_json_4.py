import requests

try:
    r = requests.get("http://localhost:8001/api/inventory/products")
    print(r.status_code)
    print(r.text[:500])
except Exception as e:
    print(e)
