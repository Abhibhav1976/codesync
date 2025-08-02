import requests
import sys
import json
import time
from datetime import datetime

class CodeEditorAPITester:
    def __init__(self, base_url="https://5b1461cf-3c8c-42b1-84f4-03abe3bb8b73.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.room_id = None
        self.user_id = f"test_user_{int(time.time())}"

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}" if not endpoint.startswith('http') else endpoint
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        if data:
            print(f"   Data: {json.dumps(data, indent=2)}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)

            print(f"   Response Status: {response.status_code}")
            
            try:
                response_data = response.json()
                print(f"   Response Data: {json.dumps(response_data, indent=2)}")
            except:
                print(f"   Response Text: {response.text[:200]}...")

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")

            return success, response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        success, response = self.run_test(
            "Root API Endpoint",
            "GET",
            "",
            200
        )
        return success

    def test_create_room(self):
        """Test creating a new room"""
        success, response = self.run_test(
            "Create Room",
            "POST",
            "rooms",
            200,
            data={
                "name": "Test Room",
                "language": "javascript"
            }
        )
        
        if success and isinstance(response, dict) and 'id' in response:
            self.room_id = response['id']
            print(f"   Created room with ID: {self.room_id}")
            return True
        return False

    def test_get_room(self):
        """Test getting room details"""
        if not self.room_id:
            print("❌ No room ID available for testing")
            return False
            
        success, response = self.run_test(
            "Get Room Details",
            "GET",
            f"rooms/{self.room_id}",
            200
        )
        return success

    def test_join_room(self):
        """Test joining a room with user_name (Phase 1 feature)"""
        if not self.room_id:
            print("❌ No room ID available for testing")
            return False
            
        success, response = self.run_test(
            "Join Room with User Name",
            "POST",
            "rooms/join",
            200,
            data={
                "room_id": self.room_id,
                "user_id": self.user_id,
                "user_name": "Alice_Developer"
            }
        )
        
        # Verify user_name is returned in response
        if success and isinstance(response, dict):
            if 'user_name' in response and response['user_name'] == "Alice_Developer":
                print("✅ User name correctly returned in join response")
            else:
                print("❌ User name not found in join response")
                return False
        
        return success

    def test_update_code(self):
        """Test updating code in a room with user_name (Phase 1 feature)"""
        if not self.room_id:
            print("❌ No room ID available for testing")
            return False
            
        test_code = "console.log('Hello from Alice!');"
        success, response = self.run_test(
            "Update Code with User Name",
            "POST",
            "rooms/code",
            200,
            data={
                "room_id": self.room_id,
                "code": test_code,
                "user_id": self.user_id,
                "user_name": "Alice_Developer"
            }
        )
        return success

    def test_update_cursor(self):
        """Test updating cursor position"""
        if not self.room_id:
            print("❌ No room ID available for testing")
            return False
            
        success, response = self.run_test(
            "Update Cursor Position",
            "POST",
            "rooms/cursor",
            200,
            data={
                "room_id": self.room_id,
                "user_id": self.user_id,
                "position": {
                    "line": 1,
                    "column": 10
                }
            }
        )
        return success

    def test_save_room(self):
        """Test saving room data"""
        if not self.room_id:
            print("❌ No room ID available for testing")
            return False
            
        success, response = self.run_test(
            "Save Room",
            "POST",
            f"rooms/{self.room_id}/save",
            200
        )
        return success

    def test_sse_endpoint(self):
        """Test SSE endpoint accessibility (just check if it responds)"""
        print(f"\n🔍 Testing SSE Endpoint...")
        sse_url = f"{self.base_url}/sse/{self.user_id}"
        print(f"   URL: {sse_url}")
        
        try:
            # Just test if the endpoint is accessible (don't wait for stream)
            response = requests.get(sse_url, timeout=5, stream=True)
            print(f"   Response Status: {response.status_code}")
            print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
            
            if response.status_code == 200:
                print("✅ SSE endpoint is accessible")
                self.tests_passed += 1
            else:
                print(f"❌ SSE endpoint failed - Status: {response.status_code}")
                
            self.tests_run += 1
            return response.status_code == 200
            
        except Exception as e:
            print(f"❌ SSE endpoint failed - Error: {str(e)}")
            self.tests_run += 1
            return False

    def test_invalid_room_join(self):
        """Test joining a non-existent room"""
        success, response = self.run_test(
            "Join Invalid Room",
            "POST",
            "rooms/join",
            200,  # API returns 200 with error message
            data={
                "room_id": "invalid-room-id",
                "user_id": self.user_id
            }
        )
        
        # Check if error message is returned
        if success and isinstance(response, dict) and 'error' in response:
            print("✅ Correctly returned error for invalid room")
            return True
        else:
            print("❌ Should have returned error for invalid room")
            return False

def main():
    print("🚀 Starting Real-Time Code Editor API Tests")
    print("=" * 60)
    
    tester = CodeEditorAPITester()
    
    # Run all tests in sequence
    tests = [
        tester.test_root_endpoint,
        tester.test_create_room,
        tester.test_get_room,
        tester.test_join_room,
        tester.test_update_code,
        tester.test_update_cursor,
        tester.test_save_room,
        tester.test_sse_endpoint,
        tester.test_invalid_room_join
    ]
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
            tester.tests_run += 1
        
        time.sleep(0.5)  # Small delay between tests
    
    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 BACKEND API TEST RESULTS")
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Tests Failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed / tester.tests_run * 100):.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All backend tests passed!")
        return 0
    else:
        print("⚠️  Some backend tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())