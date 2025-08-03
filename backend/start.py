#!/usr/bin/env python3
"""
Render deployment startup script for CodeSync backend
"""

import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    
    print(f"Starting CodeSync backend on port {port}")
    print(f"MongoDB URL configured: {os.environ.get('MONGO_URL', 'Not set')[:50]}...")
    
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=port,
        workers=1,
        access_log=True,
        log_level="info"
    )