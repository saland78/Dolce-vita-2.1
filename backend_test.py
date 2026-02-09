import requests
import sys
import json
from datetime import datetime

class BakeryAPITester:
    def __init__(self, base_url="https://sweettrack-4.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)

            success = response.status_code == expected_status
            result = {
                "test_name": name,
                "endpoint": endpoint,
                "method": method,
                "expected_status": expected_status,
                "actual_status": response.status_code,
                "success": success,
                "response_data": None,
                "error": None
            }

            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    result["response_data"] = response.json()
                except:
                    result["response_data"] = response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    result["error"] = response.json()
                except:
                    result["error"] = response.text

            self.test_results.append(result)
            return success, result.get("response_data", {})

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            result = {
                "test_name": name,
                "endpoint": endpoint,
                "method": method,
                "expected_status": expected_status,
                "actual_status": None,
                "success": False,
                "response_data": None,
                "error": str(e)
            }
            self.test_results.append(result)
            return False, {}

    def test_api_root(self):
        """Test API root endpoint"""
        return self.run_test("API Root", "GET", "api/", 200)

    def test_get_stats(self):
        """Test getting order statistics"""
        return self.run_test("Get Order Stats", "GET", "api/orders/stats", 200)

    def test_get_orders(self):
        """Test getting all orders"""
        return self.run_test("Get All Orders", "GET", "api/orders", 200)

    def test_simulate_order(self):
        """Test simulating a random order"""
        return self.run_test("Simulate Order", "POST", "api/orders/simulate", 200)

    def test_get_ingredients(self):
        """Test getting ingredients"""
        return self.run_test("Get Ingredients", "GET", "api/inventory/ingredients", 200)

    def test_seed_inventory(self):
        """Test seeding inventory"""
        return self.run_test("Seed Inventory", "POST", "api/inventory/seed", 200)

    def test_get_products(self):
        """Test getting products"""
        return self.run_test("Get Products", "GET", "api/inventory/products", 200)

    def test_order_status_update(self):
        """Test updating order status"""
        # First create an order
        success, order_data = self.test_simulate_order()
        if not success or not order_data:
            print("❌ Cannot test status update - order creation failed")
            return False, {}
        
        order_id = order_data.get('_id')
        if not order_id:
            print("❌ Cannot test status update - no order ID returned")
            return False, {}

        # Test status update
        return self.run_test(
            "Update Order Status", 
            "PUT", 
            f"api/orders/{order_id}/status?status=in_production", 
            200
        )

def main():
    print("🧁 Starting BakeryOS API Testing...")
    tester = BakeryAPITester()

    # Test sequence
    print("\n=== Basic API Tests ===")
    tester.test_api_root()
    
    print("\n=== Order Management Tests ===")
    tester.test_get_stats()
    tester.test_get_orders()
    tester.test_simulate_order()
    tester.test_order_status_update()
    
    print("\n=== Inventory Management Tests ===")
    tester.test_seed_inventory()
    tester.test_get_ingredients()
    tester.test_get_products()

    # Print summary
    print(f"\n📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    
    # Save detailed results
    with open('/app/backend_test_results.json', 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_tests": tester.tests_run,
            "passed_tests": tester.tests_passed,
            "success_rate": (tester.tests_passed / tester.tests_run * 100) if tester.tests_run > 0 else 0,
            "test_details": tester.test_results
        }, f, indent=2)
    
    return 0 if tester.tests_passed == tester.tests_run else 1

if __name__ == "__main__":
    sys.exit(main())