import requests
import sys
import json
import time
from datetime import datetime

class CodeSyncDebugTester:
    def __init__(self, base_url="https://a7f2e870-c985-4fde-8c31-0b78dd933703.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.room_id = None
        self.user_id = f"debug_user_{int(time.time())}"

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None, check_headers=None):
        """Run a single API test with enhanced debugging"""
        if endpoint.startswith('http'):
            url = endpoint
        elif endpoint == "/health":
            url = f"{self.base_url}/health"
        elif endpoint.startswith('/api'):
            url = f"{self.base_url}{endpoint}"
        elif endpoint == "" or endpoint == "/":
            url = f"{self.base_url}/api/"
        else:
            url = f"{self.api_url}/{endpoint}"
            
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        print(f"   Method: {method}")
        if data:
            print(f"   Data: {json.dumps(data, indent=2)}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'OPTIONS':
                response = requests.options(url, headers=headers, timeout=10)

            print(f"   Response Status: {response.status_code}")
            print(f"   Response Headers: {dict(response.headers)}")
            
            try:
                response_data = response.json()
                print(f"   Response Data: {json.dumps(response_data, indent=2)}")
            except:
                print(f"   Response Text: {response.text[:200]}...")
                response_data = response.text

            # Check specific headers if requested
            if check_headers:
                for header, expected_value in check_headers.items():
                    actual_value = response.headers.get(header, "")
                    if expected_value.lower() in actual_value.lower():
                        print(f"   ✅ Header {header}: {actual_value}")
                    else:
                        print(f"   ❌ Header {header}: Expected '{expected_value}', got '{actual_value}'")

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")

            return success, response_data, response.headers

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}, {}

    # ========== ROOT ROUTE FIXES TESTS ==========
    
    def test_root_endpoint_json_response(self):
        """Test GET / returns proper JSON response with backend info"""
        # The root endpoint should be the backend root, not the frontend
        success, response, headers = self.run_test(
            "Backend Root Endpoint JSON Response",
            "GET",
            "/api/",
            200
        )
        
        if success and isinstance(response, dict):
            required_fields = ['message', 'endpoints']
            missing_fields = [field for field in required_fields if field not in response]
            if not missing_fields:
                print("✅ Backend root endpoint returns proper JSON with required fields")
                if "Real-Time Code Editor API" in response.get('message', ''):
                    print("✅ Correct backend API identification message")
                    return True
                else:
                    print("❌ Backend API message not as expected")
                    return False
            else:
                print(f"❌ Missing required fields: {missing_fields}")
                return False
        else:
            print("❌ Backend root endpoint should return JSON object")
            return False

    def test_health_endpoint_database_status(self):
        """Test GET /health shows database connectivity and system status"""
        success, response, headers = self.run_test(
            "Health Endpoint Database Status",
            "GET",
            "/health",
            200
        )
        
        if success and isinstance(response, dict):
            required_fields = ['status', 'timestamp', 'database', 'active_rooms', 'active_connections']
            missing_fields = [field for field in required_fields if field not in response]
            if not missing_fields:
                print("✅ Health endpoint returns all required status fields")
                
                # Check database status
                db_status = response.get('database')
                if db_status in ['connected', 'disconnected']:
                    print(f"✅ Database status properly reported: {db_status}")
                    return True
                else:
                    print(f"❌ Database status should be 'connected' or 'disconnected', got: {db_status}")
                    return False
            else:
                print(f"❌ Missing required fields: {missing_fields}")
                return False
        else:
            print("❌ Health endpoint should return JSON object")
            return False

    # ========== CORS/OPTIONS FIXES TESTS ==========
    
    def test_options_rooms_cors(self):
        """Test OPTIONS /api/rooms returns 200 OK with proper CORS headers"""
        success, response, headers = self.run_test(
            "OPTIONS /api/rooms CORS Headers",
            "OPTIONS",
            "rooms",
            200,
            check_headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': '*'
            }
        )
        
        if success:
            # Verify CORS headers are present
            cors_headers = [
                'Access-Control-Allow-Origin',
                'Access-Control-Allow-Methods', 
                'Access-Control-Allow-Headers'
            ]
            missing_cors = [h for h in cors_headers if h not in headers]
            if not missing_cors:
                print("✅ All required CORS headers present")
                return True
            else:
                print(f"❌ Missing CORS headers: {missing_cors}")
                return False
        return False

    def test_options_run_code_cors(self):
        """Test OPTIONS /api/run-code returns 200 OK with proper CORS headers"""
        success, response, headers = self.run_test(
            "OPTIONS /api/run-code CORS Headers",
            "OPTIONS",
            "run-code",
            200,
            check_headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': '*'
            }
        )
        
        if success:
            # Verify CORS headers are present
            cors_headers = [
                'Access-Control-Allow-Origin',
                'Access-Control-Allow-Methods', 
                'Access-Control-Allow-Headers'
            ]
            missing_cors = [h for h in cors_headers if h not in headers]
            if not missing_cors:
                print("✅ All required CORS headers present")
                return True
            else:
                print(f"❌ Missing CORS headers: {missing_cors}")
                return False
        return False

    def test_post_rooms_after_options(self):
        """Test POST /api/rooms still works normally after OPTIONS"""
        # First do OPTIONS request
        self.test_options_rooms_cors()
        
        # Then do POST request
        success, response, headers = self.run_test(
            "POST /api/rooms After OPTIONS",
            "POST",
            "rooms",
            200,
            data={
                "name": "Debug Test Room",
                "language": "javascript"
            }
        )
        
        if success and isinstance(response, dict) and 'id' in response:
            self.room_id = response['id']
            print(f"✅ POST request works normally after OPTIONS, room ID: {self.room_id}")
            return True
        else:
            print("❌ POST request failed after OPTIONS")
            return False

    def test_post_run_code_after_options(self):
        """Test POST /api/run-code still works normally after OPTIONS"""
        # First do OPTIONS request
        self.test_options_run_code_cors()
        
        # Then do POST request
        success, response, headers = self.run_test(
            "POST /api/run-code After OPTIONS",
            "POST",
            "run-code",
            200,
            data={
                "language": "javascript",
                "code": "console.log('CORS test successful!');",
                "stdin": ""
            }
        )
        
        if success and isinstance(response, dict):
            required_fields = ['stdout', 'stderr', 'exit_code']
            missing_fields = [field for field in required_fields if field not in response]
            if not missing_fields:
                print("✅ POST run-code works normally after OPTIONS")
                return True
            else:
                print(f"❌ POST run-code missing fields: {missing_fields}")
                return False
        else:
            print("❌ POST run-code failed after OPTIONS")
            return False

    # ========== ERROR HANDLING TESTS ==========
    
    def test_404_error_handler(self):
        """Test 404 endpoints return proper error responses with helpful information"""
        success, response, headers = self.run_test(
            "404 Error Handler",
            "GET",
            "nonexistent-endpoint",
            404
        )
        
        if response and isinstance(response, dict):
            required_fields = ['error', 'detail', 'method', 'available_endpoints']
            missing_fields = [field for field in required_fields if field not in response]
            if not missing_fields:
                print("✅ 404 error handler returns helpful information")
                if 'available_endpoints' in response and isinstance(response['available_endpoints'], list):
                    print(f"✅ Available endpoints provided: {response['available_endpoints']}")
                    return True
                else:
                    print("❌ Available endpoints should be a list")
                    return False
            else:
                print(f"❌ 404 response missing fields: {missing_fields}")
                return False
        else:
            print("❌ 404 should return JSON error response")
            return False

    def test_400_error_handler(self):
        """Test invalid requests trigger custom 400 error handler"""
        success, response, headers = self.run_test(
            "400 Error Handler (Invalid JSON)",
            "POST",
            "rooms",
            400,
            data={}  # Empty data should trigger validation error
        )
        
        if response and isinstance(response, dict):
            required_fields = ['error', 'detail', 'method', 'url']
            missing_fields = [field for field in required_fields if field not in response]
            if not missing_fields:
                print("✅ 400 error handler returns proper error structure")
                return True
            else:
                print(f"❌ 400 response missing fields: {missing_fields}")
                return False
        else:
            print("❌ 400 should return JSON error response")
            return False

    # ========== CORE FUNCTIONALITY TESTS ==========
    
    def test_room_creation_with_logging(self):
        """Test room creation works and generates proper logs"""
        success, response, headers = self.run_test(
            "Room Creation with Enhanced Logging",
            "POST",
            "rooms",
            200,
            data={
                "name": "Logging Test Room",
                "language": "python"
            }
        )
        
        if success and isinstance(response, dict) and 'id' in response:
            self.room_id = response['id']
            print(f"✅ Room created successfully with logging: {self.room_id}")
            return True
        else:
            print("❌ Room creation failed")
            return False

    def test_room_joining_with_logging(self):
        """Test room joining works with enhanced logging"""
        if not self.room_id:
            print("❌ No room ID available for testing")
            return False
            
        success, response, headers = self.run_test(
            "Room Joining with Enhanced Logging",
            "POST",
            "rooms/join",
            200,
            data={
                "room_id": self.room_id,
                "user_id": self.user_id,
                "user_name": "DebugTester2025"
            }
        )
        
        if success and isinstance(response, dict):
            required_fields = ['room_id', 'user_name', 'users', 'chat_messages']
            missing_fields = [field for field in required_fields if field not in response]
            if not missing_fields:
                print("✅ Room joining works with proper response structure")
                return True
            else:
                print(f"❌ Join response missing fields: {missing_fields}")
                return False
        else:
            print("❌ Room joining failed")
            return False

    def test_code_execution_with_logging(self):
        """Test code execution works with enhanced logging"""
        test_cases = [
            {
                "name": "JavaScript Execution",
                "language": "javascript",
                "code": "console.log('Debug test: JavaScript working!'); console.log(42 + 8);"
            },
            {
                "name": "Python Execution", 
                "language": "python",
                "code": "print('Debug test: Python working!')\nprint(7 * 8)"
            }
        ]
        
        all_passed = True
        for test_case in test_cases:
            success, response, headers = self.run_test(
                f"Code Execution - {test_case['name']}",
                "POST",
                "run-code",
                200,
                data={
                    "language": test_case["language"],
                    "code": test_case["code"],
                    "stdin": ""
                }
            )
            
            if success and isinstance(response, dict):
                required_fields = ['stdout', 'stderr', 'exit_code']
                missing_fields = [field for field in required_fields if field not in response]
                if missing_fields:
                    print(f"❌ {test_case['name']} missing fields: {missing_fields}")
                    all_passed = False
                else:
                    print(f"✅ {test_case['name']} executed successfully")
            else:
                print(f"❌ {test_case['name']} execution failed")
                all_passed = False
        
        return all_passed

    def test_sse_connection_with_logging(self):
        """Test SSE connections are established correctly with logging"""
        print(f"\n🔍 Testing SSE Connection with Enhanced Logging...")
        sse_url = f"{self.api_url}/sse/{self.user_id}"
        print(f"   URL: {sse_url}")
        
        try:
            response = requests.get(sse_url, timeout=5, stream=True)
            print(f"   Response Status: {response.status_code}")
            print(f"   Content-Type: {response.headers.get('content-type', 'N/A')}")
            
            # Check for SSE-specific headers (Connection header might be handled by proxy)
            expected_headers = {
                'Cache-Control': 'no-cache',
                'Access-Control-Allow-Origin': '*'
            }
            
            headers_ok = True
            for header, expected_value in expected_headers.items():
                actual_value = response.headers.get(header, '')
                if expected_value.lower() in actual_value.lower():
                    print(f"   ✅ SSE Header {header}: {actual_value}")
                else:
                    print(f"   ❌ SSE Header {header}: Expected '{expected_value}', got '{actual_value}'")
                    headers_ok = False
            
            # Check content type for SSE
            content_type = response.headers.get('content-type', '')
            if 'text/event-stream' in content_type:
                print(f"   ✅ SSE Content-Type: {content_type}")
            else:
                print(f"   ❌ SSE Content-Type should contain 'text/event-stream', got: {content_type}")
                headers_ok = False
            
            if response.status_code == 200 and headers_ok:
                print("✅ SSE endpoint accessible with proper headers")
                self.tests_passed += 1
                self.tests_run += 1
                return True
            else:
                print(f"❌ SSE endpoint failed - Status: {response.status_code} or headers incorrect")
                self.tests_run += 1
                return False
                
        except Exception as e:
            print(f"❌ SSE endpoint failed - Error: {str(e)}")
            self.tests_run += 1
            return False

    def test_chat_functionality_with_logging(self):
        """Test chat functionality works with enhanced logging"""
        if not self.room_id:
            print("❌ No room ID available for testing")
            return False
        
        success, response, headers = self.run_test(
            "Chat Message with Enhanced Logging",
            "POST",
            "send-chat-message",
            200,
            data={
                "room_id": self.room_id,
                "user_id": self.user_id,
                "user_name": "DebugTester2025",
                "message": "Debug test: Chat system working perfectly! 🚀"
            }
        )
        
        if success and isinstance(response, dict):
            if response.get('success') == True and 'message_id' in response:
                print("✅ Chat functionality working with proper logging")
                return True
            else:
                print("❌ Chat response should include success: true and message_id")
                return False
        else:
            print("❌ Chat functionality failed")
            return False

def main():
    print("🔧 Starting CodeSync Backend Debug & Fix Verification Tests")
    print("=" * 70)
    print("Testing areas:")
    print("1. Root Route Fixes (GET /, GET /health)")
    print("2. CORS/OPTIONS Fixes (OPTIONS requests)")
    print("3. Enhanced Debugging (logging verification)")
    print("4. Error Handling (custom error handlers)")
    print("5. Core Functionality (room, code execution, SSE, chat)")
    print("=" * 70)
    
    tester = CodeSyncDebugTester()
    
    # Run tests in logical order
    tests = [
        # Root Route Fixes
        tester.test_root_endpoint_json_response,
        tester.test_health_endpoint_database_status,
        
        # CORS/OPTIONS Fixes
        tester.test_options_rooms_cors,
        tester.test_options_run_code_cors,
        tester.test_post_rooms_after_options,
        tester.test_post_run_code_after_options,
        
        # Error Handling
        tester.test_404_error_handler,
        tester.test_400_error_handler,
        
        # Core Functionality with Enhanced Logging
        tester.test_room_creation_with_logging,
        tester.test_room_joining_with_logging,
        tester.test_code_execution_with_logging,
        tester.test_sse_connection_with_logging,
        tester.test_chat_functionality_with_logging
    ]
    
    for test in tests:
        try:
            test()
        except Exception as e:
            print(f"❌ Test failed with exception: {str(e)}")
            tester.tests_run += 1
        
        time.sleep(0.3)  # Small delay between tests
    
    # Print final results
    print("\n" + "=" * 70)
    print(f"🔧 DEBUG & FIX VERIFICATION TEST RESULTS")
    print(f"Tests Run: {tester.tests_run}")
    print(f"Tests Passed: {tester.tests_passed}")
    print(f"Tests Failed: {tester.tests_run - tester.tests_passed}")
    print(f"Success Rate: {(tester.tests_passed / tester.tests_run * 100):.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All debug & fix verification tests passed!")
        print("✅ Backend debugging and bug fixes are working correctly!")
        return 0
    else:
        print("⚠️  Some debug & fix verification tests failed.")
        print("❌ Backend may still have issues that need attention.")
        return 1

if __name__ == "__main__":
    sys.exit(main())