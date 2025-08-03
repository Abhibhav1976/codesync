import requests
import sys
import json
import time
from datetime import datetime

class Phase2CAPITester:
    def __init__(self, base_url="https://a7f2e870-c985-4fde-8c31-0b78dd933703.preview.emergentagent.com/api"):
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

    def setup_test_room(self):
        """Create a test room and join with a user"""
        print("🏗️  Setting up test room...")
        
        # Create room
        success, response = self.run_test(
            "Create Test Room",
            "POST",
            "rooms",
            200,
            data={
                "name": "Phase 2C Test Room",
                "language": "javascript"
            }
        )
        
        if success and isinstance(response, dict) and 'id' in response:
            self.room_id = response['id']
            print(f"   Created room with ID: {self.room_id}")
        else:
            print("❌ Failed to create test room")
            return False
        
        # Join room
        success, response = self.run_test(
            "Join Test Room",
            "POST",
            "rooms/join",
            200,
            data={
                "room_id": self.room_id,
                "user_id": self.user_id,
                "user_name": "Alice_Developer"
            }
        )
        
        return success

    def test_typing_status_true(self):
        """Test setting typing status to true"""
        if not self.room_id:
            print("❌ No room ID available for testing")
            return False
            
        success, response = self.run_test(
            "Set Typing Status True",
            "POST",
            "typing-status",
            200,
            data={
                "room_id": self.room_id,
                "user_id": self.user_id,
                "user_name": "Alice_Developer",
                "is_typing": True
            }
        )
        
        if success and isinstance(response, dict):
            if response.get('success') == True:
                print("✅ Typing status set to true successfully")
                return True
            else:
                print("❌ Response should include success: true")
                return False
        
        return success

    def test_typing_status_false(self):
        """Test setting typing status to false"""
        if not self.room_id:
            print("❌ No room ID available for testing")
            return False
            
        success, response = self.run_test(
            "Set Typing Status False",
            "POST",
            "typing-status",
            200,
            data={
                "room_id": self.room_id,
                "user_id": self.user_id,
                "user_name": "Alice_Developer",
                "is_typing": False
            }
        )
        
        if success and isinstance(response, dict):
            if response.get('success') == True:
                print("✅ Typing status set to false successfully")
                return True
            else:
                print("❌ Response should include success: true")
                return False
        
        return success

    def test_typing_status_invalid_room(self):
        """Test typing status with invalid room_id"""
        success, response = self.run_test(
            "Set Typing Status Invalid Room",
            "POST",
            "typing-status",
            200,  # API returns 200 with error message
            data={
                "room_id": "invalid-room-id",
                "user_id": self.user_id,
                "user_name": "Alice_Developer",
                "is_typing": True
            }
        )
        
        if success and isinstance(response, dict) and 'error' in response:
            if "room not found" in response['error'].lower():
                print("✅ Correctly returned 'Room not found' error for typing status")
                return True
            else:
                print("❌ Error message should be 'Room not found'")
                return False
        else:
            print("❌ Should have returned 'Room not found' error")
            return False

    def test_leave_room_valid(self):
        """Test leaving a room gracefully"""
        if not self.room_id:
            print("❌ No room ID available for testing")
            return False
        
        # Create a new user to test leaving
        leave_user_id = f"test_user_leave_{int(time.time())}"
        
        # First join the room
        success, response = self.run_test(
            "Join Room Before Leave Test",
            "POST",
            "rooms/join",
            200,
            data={
                "room_id": self.room_id,
                "user_id": leave_user_id,
                "user_name": "David_Developer"
            }
        )
        
        if not success:
            print("❌ Could not join room for leave test")
            return False
        
        # Now test leaving the room
        success, response = self.run_test(
            "Leave Room Gracefully",
            "POST",
            "leave-room",
            200,
            data={
                "room_id": self.room_id,
                "user_id": leave_user_id,
                "user_name": "David_Developer"
            }
        )
        
        if success and isinstance(response, dict):
            if response.get('success') == True and 'message' in response:
                print("✅ Left room successfully with confirmation message")
                return True
            else:
                print("❌ Response should include success: true and message")
                return False
        
        return success

    def test_leave_room_invalid(self):
        """Test leaving a non-existent room"""
        success, response = self.run_test(
            "Leave Invalid Room",
            "POST",
            "leave-room",
            200,  # API returns 200 with error message
            data={
                "room_id": "invalid-room-id",
                "user_id": self.user_id,
                "user_name": "Alice_Developer"
            }
        )
        
        if success and isinstance(response, dict) and 'error' in response:
            if "room not found" in response['error'].lower():
                print("✅ Correctly returned 'Room not found' error for leave room")
                return True
            else:
                print("❌ Error message should be 'Room not found'")
                return False
        else:
            print("❌ Should have returned 'Room not found' error")
            return False

    def test_sse_endpoint(self):
        """Test SSE endpoint accessibility"""
        print(f"\n🔍 Testing SSE Endpoint...")
        sse_url = f"{self.base_url}/sse/{self.user_id}"
        print(f"   URL: {sse_url}")
        
        try:
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

    def test_multiple_users_typing(self):
        """Test typing status with multiple users"""
        if not self.room_id:
            print("❌ No room ID available for testing")
            return False
        
        # Create additional users
        user2_id = f"test_user_typing2_{int(time.time())}"
        user3_id = f"test_user_typing3_{int(time.time())}"
        
        # Join room with additional users
        for i, (user_id, user_name) in enumerate([(user2_id, "Bob_Developer"), (user3_id, "Carol_Developer")]):
            success, response = self.run_test(
                f"Join Room User {i+2} for Typing Test",
                "POST",
                "rooms/join",
                200,
                data={
                    "room_id": self.room_id,
                    "user_id": user_id,
                    "user_name": user_name
                }
            )
            if not success:
                print(f"❌ Could not join room with user {i+2}")
                return False
        
        # Test multiple users setting typing status
        typing_tests = [
            (user2_id, "Bob_Developer", True),
            (user3_id, "Carol_Developer", True),
            (user2_id, "Bob_Developer", False),
            (user3_id, "Carol_Developer", False)
        ]
        
        all_passed = True
        for user_id, user_name, is_typing in typing_tests:
            success, response = self.run_test(
                f"Set Typing {is_typing} for {user_name}",
                "POST",
                "typing-status",
                200,
                data={
                    "room_id": self.room_id,
                    "user_id": user_id,
                    "user_name": user_name,
                    "is_typing": is_typing
                }
            )
            if not success or not response.get('success'):
                all_passed = False
                break
            time.sleep(0.1)  # Small delay between requests
        
        if all_passed:
            print("✅ Multiple users typing status updates successful")
            return True
        else:
            print("❌ Some typing status updates failed")
            return False

def main():
    print("🚀 Starting Phase 2C Backend API Tests")
    print("=" * 60)
    
    tester = Phase2CAPITester()
    
    # Setup test environment
    if not tester.setup_test_room():
        print("❌ Failed to setup test environment")
        return 1
    
    # Run Phase 2C specific tests
    tests = [
        tester.test_typing_status_true,
        tester.test_typing_status_false,
        tester.test_typing_status_invalid_room,
        tester.test_leave_room_valid,
        tester.test_leave_room_invalid,
        tester.test_sse_endpoint,
        tester.test_multiple_users_typing
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
    print(f"📊 PHASE 2C BACKEND API TEST RESULTS")
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Tests Failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed / tester.tests_run * 100):.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All Phase 2C backend tests passed!")
        return 0
    else:
        print("⚠️  Some Phase 2C backend tests failed. Check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())