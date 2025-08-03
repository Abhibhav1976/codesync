#!/usr/bin/env python3
"""
MongoDB Atlas Setup Helper Script
Run this script to properly configure your MongoDB Atlas credentials
"""

import os
import re
from urllib.parse import quote_plus

def validate_connection_string(conn_string):
    """Validate MongoDB connection string format"""
    pattern = r'^mongodb(\+srv)?:\/\/[^:]+:[^@]+@[^\/]+\/?\?.*$'
    return bool(re.match(pattern, conn_string))

def extract_credentials_from_url(mongo_url):
    """Extract username, password, and cluster from MongoDB URL"""
    try:
        # Pattern to extract credentials
        pattern = r'mongodb\+srv:\/\/([^:]+):([^@]+)@([^\/\?]+)'
        match = re.match(pattern, mongo_url)
        
        if match:
            username, password, cluster = match.groups()
            return username, password, cluster
        return None, None, None
    except Exception:
        return None, None, None

def create_env_file():
    """Create or update .env file with MongoDB credentials"""
    print("🔧 MongoDB Atlas Credential Setup")
    print("=" * 50)
    
    # Option 1: Full connection string
    print("Option 1: Provide full MongoDB Atlas connection string")
    print("Example: mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority")
    full_url = input("Enter full MongoDB URL (or press Enter to skip): ").strip()
    
    if full_url and validate_connection_string(full_url):
        username, password, cluster = extract_credentials_from_url(full_url)
        if username and password and cluster:
            print(f"✅ Extracted credentials successfully")
            print(f"   Username: {username}")
            print(f"   Cluster: {cluster}")
        else:
            print("❌ Could not extract credentials from URL")
            return False
    else:
        # Option 2: Individual credentials
        print("\nOption 2: Provide individual credentials")
        username = input("MongoDB Username: ").strip()
        password = input("MongoDB Password: ").strip()
        cluster = input("MongoDB Cluster (e.g., cluster0.abcde.mongodb.net): ").strip()
        
        if not all([username, password, cluster]):
            print("❌ All fields are required")
            return False
        
        # Construct full URL
        username_encoded = quote_plus(username)
        password_encoded = quote_plus(password)
        full_url = f"mongodb+srv://{username_encoded}:{password_encoded}@{cluster}/?retryWrites=true&w=majority&appName=codesync"
    
    # Database name
    db_name = input("Database name (default: codesync): ").strip() or "codesync"
    
    # Write to .env file
    env_content = f"""MONGO_URL="{full_url}"
DB_NAME="{db_name}"

# Alternative credential format (for fallback)
MONGO_USERNAME="{username}"
MONGO_PASSWORD="{password}"
MONGO_CLUSTER="{cluster}"
"""
    
    with open('/app/backend/.env', 'w') as f:
        f.write(env_content)
    
    print("✅ Created /app/backend/.env file")
    
    # Create Render environment variable instructions
    render_env = f"""
🚀 RENDER DEPLOYMENT ENVIRONMENT VARIABLES:

Add these in your Render service Environment section:

MONGO_URL = {full_url}
DB_NAME = {db_name}

Alternative format (backup):
MONGO_USERNAME = {username}
MONGO_PASSWORD = {password}
MONGO_CLUSTER = {cluster}
"""
    
    with open('/app/RENDER_ENV_VARS.txt', 'w') as f:
        f.write(render_env)
    
    print("✅ Created /app/RENDER_ENV_VARS.txt with Render deployment variables")
    return True

def test_connection():
    """Test MongoDB connection with current credentials"""
    print("\n🧪 Testing MongoDB Connection...")
    
    import asyncio
    from mongo_config import mongo_config
    
    async def test():
        success = await mongo_config.connect()
        if success:
            print("✅ MongoDB connection successful!")
            
            # Test basic operations
            try:
                db = mongo_config.get_database()
                test_doc = {"test": "connection", "timestamp": "2025-01-01"}
                result = await db.connection_test.insert_one(test_doc)
                await db.connection_test.delete_one({"_id": result.inserted_id})
                print("✅ Database operations working!")
                return True
            except Exception as e:
                print(f"❌ Database operations failed: {e}")
                return False
        else:
            print("❌ MongoDB connection failed!")
            return False
    
    return asyncio.run(test())

def main():
    """Main setup function"""
    print("MongoDB Atlas Setup for CodeSync")
    print("=" * 40)
    
    # Check if .env exists
    if os.path.exists('/app/backend/.env'):
        print("📁 Found existing .env file")
        choice = input("Overwrite existing configuration? (y/N): ").lower()
        if choice != 'y':
            print("Setup cancelled")
            return
    
    # Create credentials
    if create_env_file():
        print("\n" + "=" * 50)
        
        # Test connection
        test_choice = input("Test connection now? (Y/n): ").lower()
        if test_choice != 'n':
            if test_connection():
                print("\n🎉 Setup completed successfully!")
                print("\n📋 Next Steps:")
                print("1. Copy environment variables from RENDER_ENV_VARS.txt")
                print("2. Add them to your Render service")
                print("3. Deploy your service")
            else:
                print("\n⚠️  Setup completed but connection test failed")
                print("Please check your MongoDB Atlas credentials and network access")

if __name__ == "__main__":
    main()