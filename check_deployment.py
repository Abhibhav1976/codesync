#!/usr/bin/env python3
"""
Deployment health check script for CodeSync
"""

import asyncio
import httpx
import sys
from datetime import datetime

async def check_backend_health(base_url):
    """Check backend API health"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Check health endpoint
            response = await client.get(f"{base_url}/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Backend Health: {data.get('status', 'Unknown')}")
                print(f"   Database: {data.get('database', 'Unknown')}")
                return True
            else:
                print(f"❌ Backend Health Check Failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ Backend Connection Failed: {str(e)}")
        return False

async def check_api_endpoints(base_url):
    """Check critical API endpoints"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test room creation
            room_data = {"name": "health-check", "language": "javascript"}
            response = await client.post(f"{base_url}/api/rooms", json=room_data)
            
            if response.status_code == 200:
                print("✅ Room Creation API: Working")
                room = response.json()
                room_id = room['id']
                
                # Test run code
                code_data = {"language": "javascript", "code": "console.log('Health check');"}
                response = await client.post(f"{base_url}/api/run-code", json=code_data)
                
                if response.status_code == 200:
                    print("✅ Code Execution API: Working")
                    return True
                else:
                    print(f"❌ Code Execution API Failed: {response.status_code}")
                    return False
            else:
                print(f"❌ Room Creation API Failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ API Test Failed: {str(e)}")
        return False

async def main():
    """Main health check function"""
    print(f"CodeSync Deployment Health Check - {datetime.now()}")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        print("Usage: python check_deployment.py <backend_url>")
        print("Example: python check_deployment.py https://your-app.onrender.com")
        sys.exit(1)
    
    backend_url = sys.argv[1].rstrip('/')
    
    print(f"Checking: {backend_url}")
    print("-" * 50)
    
    # Check backend health
    backend_ok = await check_backend_health(backend_url)
    
    # Check API endpoints
    api_ok = await check_api_endpoints(backend_url)
    
    print("-" * 50)
    if backend_ok and api_ok:
        print("✅ All systems operational!")
        sys.exit(0)
    else:
        print("❌ Some systems are not working properly")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())