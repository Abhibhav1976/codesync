import requests
import sys
import json
import time
from datetime import datetime

class CodeEditorAPITester:
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
        """Test updating cursor position with user_name (Phase 1 feature)"""
        if not self.room_id:
            print("❌ No room ID available for testing")
            return False
            
        success, response = self.run_test(
            "Update Cursor Position with User Name",
            "POST",
            "rooms/cursor",
            200,
            data={
                "room_id": self.room_id,
                "user_id": self.user_id,
                "user_name": "Alice_Developer",
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

    def test_run_code_javascript(self):
        """Test running JavaScript code (Phase 1 feature)"""
        js_code = "console.log('Hello from JavaScript!');\nconsole.log(2 + 3);"
        
        success, response = self.run_test(
            "Run JavaScript Code",
            "POST",
            "run-code",
            200,
            data={
                "language": "javascript",
                "code": js_code,
                "stdin": ""
            }
        )
        
        # Verify response format
        if success and isinstance(response, dict):
            required_fields = ['stdout', 'stderr', 'exit_code']
            missing_fields = [field for field in required_fields if field not in response]
            if missing_fields:
                print(f"❌ Missing fields in response: {missing_fields}")
                return False
            else:
                print("✅ Run code response has correct format")
        
        return success

    def test_run_code_python(self):
        """Test running Python code (Phase 1 feature)"""
        python_code = "print('Hello from Python!')\nprint(5 * 7)"
        
        success, response = self.run_test(
            "Run Python Code",
            "POST",
            "run-code",
            200,
            data={
                "language": "python",
                "code": python_code,
                "stdin": ""
            }
        )
        
        # Verify response format
        if success and isinstance(response, dict):
            required_fields = ['stdout', 'stderr', 'exit_code']
            missing_fields = [field for field in required_fields if field not in response]
            if missing_fields:
                print(f"❌ Missing fields in response: {missing_fields}")
                return False
            else:
                print("✅ Run code response has correct format")
        
        return success

    def test_run_code_invalid_language(self):
        """Test running code with invalid language (Phase 1 error handling)"""
        success, response = self.run_test(
            "Run Code with Invalid Language",
            "POST",
            "run-code",
            200,  # API should return 200 with error in response
            data={
                "language": "invalid_language",
                "code": "print('test')",
                "stdin": ""
            }
        )
        
        # Should return error response but with 200 status
        if success and isinstance(response, dict):
            if 'error' in response or response.get('exit_code', 0) != 0:
                print("✅ Correctly handled invalid language")
                return True
            else:
                print("❌ Should have returned error for invalid language")
                return False
        
        return success

    def test_run_code_syntax_error(self):
        """Test running code with syntax error (Phase 1 error handling)"""
        bad_code = "console.log('missing quote);"
        
        success, response = self.run_test(
            "Run Code with Syntax Error",
            "POST",
            "run-code",
            200,
            data={
                "language": "javascript",
                "code": bad_code,
                "stdin": ""
            }
        )
        
        # Should return with non-zero exit code or stderr content
        if success and isinstance(response, dict):
            if response.get('exit_code', 0) != 0 or response.get('stderr', ''):
                print("✅ Correctly handled syntax error")
                return True
            else:
                print("❌ Should have returned error for syntax error")
                return False
        
        return success
    def test_invalid_room_join(self):
        """Test joining a non-existent room with user_name"""
        success, response = self.run_test(
            "Join Invalid Room",
            "POST",
            "rooms/join",
            200,  # API returns 200 with error message
            data={
                "room_id": "invalid-room-id",
                "user_id": self.user_id,
                "user_name": "Alice_Developer"
            }
        )
        
        # Check if error message is returned
        if success and isinstance(response, dict) and 'error' in response:
            print("✅ Correctly returned error for invalid room")
            return True
        else:
            print("❌ Should have returned error for invalid room")
            return False

    # ========== PHASE 2A CHAT FUNCTIONALITY TESTS ==========
    
    def test_send_chat_message_valid(self):
        """Test sending a valid chat message (Phase 2A feature)"""
        if not self.room_id:
            print("❌ No room ID available for testing")
            return False
            
        success, response = self.run_test(
            "Send Valid Chat Message",
            "POST",
            "send-chat-message",
            200,
            data={
                "room_id": self.room_id,
                "user_id": self.user_id,
                "user_name": "Alice_Developer",
                "message": "Hello everyone! This is a test message."
            }
        )
        
        # Verify response includes success and message_id
        if success and isinstance(response, dict):
            if response.get('success') == True and 'message_id' in response:
                print("✅ Chat message sent successfully with message_id")
                return True
            else:
                print("❌ Response should include success: true and message_id")
                return False
        
        return success

    def test_send_chat_message_empty(self):
        """Test sending empty chat message (should return error)"""
        if not self.room_id:
            print("❌ No room ID available for testing")
            return False
            
        success, response = self.run_test(
            "Send Empty Chat Message",
            "POST",
            "send-chat-message",
            200,  # API returns 200 with error message
            data={
                "room_id": self.room_id,
                "user_id": self.user_id,
                "user_name": "Alice_Developer",
                "message": ""
            }
        )
        
        # Should return error for empty message
        if success and isinstance(response, dict) and 'error' in response:
            if "empty" in response['error'].lower():
                print("✅ Correctly rejected empty message")
                return True
            else:
                print("❌ Error message should mention empty message")
                return False
        else:
            print("❌ Should have returned error for empty message")
            return False

    def test_send_chat_message_too_long(self):
        """Test sending message over 200 characters (should return error)"""
        if not self.room_id:
            print("❌ No room ID available for testing")
            return False
            
        long_message = "A" * 201  # 201 characters
        success, response = self.run_test(
            "Send Long Chat Message (>200 chars)",
            "POST",
            "send-chat-message",
            200,  # API returns 200 with error message
            data={
                "room_id": self.room_id,
                "user_id": self.user_id,
                "user_name": "Alice_Developer",
                "message": long_message
            }
        )
        
        # Should return error for message too long
        if success and isinstance(response, dict) and 'error' in response:
            if "long" in response['error'].lower() or "200" in response['error']:
                print("✅ Correctly rejected message over 200 characters")
                return True
            else:
                print("❌ Error message should mention message length limit")
                return False
        else:
            print("❌ Should have returned error for message too long")
            return False

    def test_send_chat_message_invalid_room(self):
        """Test sending chat message to non-existent room"""
        success, response = self.run_test(
            "Send Chat Message to Invalid Room",
            "POST",
            "send-chat-message",
            200,  # API returns 200 with error message
            data={
                "room_id": "invalid-room-id",
                "user_id": self.user_id,
                "user_name": "Alice_Developer",
                "message": "This should fail"
            }
        )
        
        # Should return "Room not found" error
        if success and isinstance(response, dict) and 'error' in response:
            if "room not found" in response['error'].lower():
                print("✅ Correctly returned 'Room not found' error")
                return True
            else:
                print("❌ Error message should be 'Room not found'")
                return False
        else:
            print("❌ Should have returned 'Room not found' error")
            return False

    def test_chat_messages_in_join_response(self):
        """Test that joining a room returns existing chat messages"""
        if not self.room_id:
            print("❌ No room ID available for testing")
            return False
        
        # First, send a few chat messages
        messages_sent = []
        for i in range(3):
            message_text = f"Test message {i+1} from Alice"
            success, response = self.run_test(
                f"Send Chat Message {i+1} for Join Test",
                "POST",
                "send-chat-message",
                200,
                data={
                    "room_id": self.room_id,
                    "user_id": self.user_id,
                    "user_name": "Alice_Developer",
                    "message": message_text
                }
            )
            if success:
                messages_sent.append(message_text)
            time.sleep(0.1)  # Small delay between messages
        
        # Now join the room with a different user and check if messages are returned
        new_user_id = f"test_user_2_{int(time.time())}"
        success, response = self.run_test(
            "Join Room and Check Chat History",
            "POST",
            "rooms/join",
            200,
            data={
                "room_id": self.room_id,
                "user_id": new_user_id,
                "user_name": "Bob_Developer"
            }
        )
        
        # Verify chat_messages are included in response
        if success and isinstance(response, dict):
            if 'chat_messages' in response:
                chat_messages = response['chat_messages']
                if isinstance(chat_messages, list) and len(chat_messages) >= len(messages_sent):
                    print(f"✅ Join response includes {len(chat_messages)} chat messages")
                    
                    # Verify message structure
                    if chat_messages:
                        last_message = chat_messages[-1]
                        required_fields = ['id', 'user_id', 'user_name', 'message', 'timestamp']
                        missing_fields = [field for field in required_fields if field not in last_message]
                        if not missing_fields:
                            print("✅ Chat message structure is correct")
                            return True
                        else:
                            print(f"❌ Chat message missing fields: {missing_fields}")
                            return False
                    else:
                        print("✅ Chat messages array is present (empty)")
                        return True
                else:
                    print(f"❌ Expected at least {len(messages_sent)} messages, got {len(chat_messages)}")
                    return False
            else:
                print("❌ Join response should include chat_messages field")
                return False
        
        return success

    def test_chat_message_limit(self):
        """Test that chat messages are limited to last 100 messages"""
        if not self.room_id:
            print("❌ No room ID available for testing")
            return False
        
        print(f"\n🔍 Testing Chat Message Limit (sending 105 messages)...")
        
        # Send 105 messages to test the 100 message limit
        messages_sent = 0
        for i in range(105):
            success, response = self.run_test(
                f"Send Message {i+1}/105 for Limit Test",
                "POST",
                "send-chat-message",
                200,
                data={
                    "room_id": self.room_id,
                    "user_id": self.user_id,
                    "user_name": "Alice_Developer",
                    "message": f"Limit test message {i+1}"
                }
            )
            if success:
                messages_sent += 1
            
            # Don't print individual test results for this bulk operation
            if i % 20 == 0:
                print(f"   Sent {i+1}/105 messages...")
        
        print(f"   Successfully sent {messages_sent}/105 messages")
        
        # Now join room and check message count
        new_user_id = f"test_user_limit_{int(time.time())}"
        success, response = self.run_test(
            "Join Room and Check Message Limit",
            "POST",
            "rooms/join",
            200,
            data={
                "room_id": self.room_id,
                "user_id": new_user_id,
                "user_name": "Charlie_Developer"
            }
        )
        
        if success and isinstance(response, dict) and 'chat_messages' in response:
            message_count = len(response['chat_messages'])
            if message_count <= 100:
                print(f"✅ Message limit enforced - {message_count} messages returned (≤100)")
                return True
            else:
                print(f"❌ Too many messages returned - {message_count} (should be ≤100)")
                return False
        else:
            print("❌ Could not verify message limit")
            return False

    # ========== PHASE 2C TYPING STATUS AND LEAVE ROOM TESTS ==========
    
    def test_typing_status_true(self):
        """Test setting typing status to true (Phase 2C feature)"""
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
        
        # Verify response includes success
        if success and isinstance(response, dict):
            if response.get('success') == True:
                print("✅ Typing status set to true successfully")
                return True
            else:
                print("❌ Response should include success: true")
                return False
        
        return success

    def test_typing_status_false(self):
        """Test setting typing status to false (Phase 2C feature)"""
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
        
        # Verify response includes success
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
        
        # Should return "Room not found" error
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
        """Test leaving a room gracefully (Phase 2C feature)"""
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
        
        # Verify response includes success and message
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
        
        # Should return "Room not found" error
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

    def test_typing_status_multiple_users(self):
        """Test typing status with multiple users in room"""
        if not self.room_id:
            print("❌ No room ID available for testing")
            return False
        
        # Create additional users for testing
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
        tester.test_run_code_javascript,
        tester.test_run_code_python,
        tester.test_run_code_invalid_language,
        tester.test_run_code_syntax_error,
        tester.test_invalid_room_join,
        # Phase 2A Chat functionality tests
        tester.test_send_chat_message_valid,
        tester.test_send_chat_message_empty,
        tester.test_send_chat_message_too_long,
        tester.test_send_chat_message_invalid_room,
        tester.test_chat_messages_in_join_response,
        tester.test_chat_message_limit,
        # Phase 2C Typing Status and Leave Room tests
        tester.test_typing_status_true,
        tester.test_typing_status_false,
        tester.test_typing_status_invalid_room,
        tester.test_leave_room_valid,
        tester.test_leave_room_invalid,
        tester.test_typing_status_multiple_users
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