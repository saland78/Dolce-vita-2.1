import requests
import warnings

# Suppress SSL warnings for clearer output
warnings.filterwarnings("ignore")

URL = "https://pasticceria.andreasalardi.it"
API_ENDPOINT = f"{URL}/wp-json/wc/v3/products"

def probe(headers, description):
    print(f"\n--- Testing: {description} ---")
    try:
        resp = requests.get(API_ENDPOINT, headers=headers, verify=False, timeout=10)
        print(f"Status Code: {resp.status_code}")
        print("Response Snippet:")
        print(resp.text[:500]) # First 500 chars
    except Exception as e:
        print(f"Connection Error: {e}")

# 1. Standard Python User-Agent
probe({}, "Default Python User-Agent")

# 2. Browser User-Agent
headers_browser = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
probe(headers_browser, "Browser User-Agent")

# 3. Check Homepage (maybe only API is blocked?)
print("\n--- Testing Homepage Root ---")
try:
    resp = requests.get(URL, headers=headers_browser, verify=False, timeout=10)
    print(f"Status Code: {resp.status_code}")
except Exception as e:
    print(f"Error: {e}")
