"""
MongoDB Atlas Connection Configuration with Authentication Handling
"""

import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import OperationFailure, ServerSelectionTimeoutError
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

class MongoDBConfig:
    def __init__(self):
        self.client = None
        self.db = None
        self.connected = False
        
    async def connect(self):
        """Connect to MongoDB with multiple fallback options"""
        
        # Try different connection methods in order of preference
        connection_methods = [
            self._connect_with_env_url,
            self._connect_with_separate_credentials,
            self._connect_local_fallback
        ]
        
        for method in connection_methods:
            try:
                logger.info(f"Attempting connection with method: {method.__name__}")
                success = await method()
                if success:
                    self.connected = True
                    logger.info(f"✅ MongoDB connected successfully using {method.__name__}")
                    return True
            except Exception as e:
                logger.warning(f"❌ {method.__name__} failed: {str(e)}")
                continue
        
        logger.error("❌ All MongoDB connection methods failed")
        return False
    
    async def _connect_with_env_url(self):
        """Try connection with MONGO_URL environment variable"""
        mongo_url = os.environ.get('MONGO_URL')
        if not mongo_url:
            raise ValueError("MONGO_URL not set")
            
        self.client = AsyncIOMotorClient(
            mongo_url,
            tls=True,
            tlsAllowInvalidCertificates=False,
            serverSelectionTimeoutMS=10000,
            connectTimeoutMS=10000,
        )
        
        # Test connection
        await self.client.admin.command('ping')
        self.db = self.client[os.environ.get('DB_NAME', 'codesync')]
        await self.db.command("ping")
        return True
    
    async def _connect_with_separate_credentials(self):
        """Try connection with separate credential environment variables"""
        username = os.environ.get('MONGO_USERNAME')
        password = os.environ.get('MONGO_PASSWORD') 
        cluster = os.environ.get('MONGO_CLUSTER')
        
        if not all([username, password, cluster]):
            raise ValueError("Missing MONGO_USERNAME, MONGO_PASSWORD, or MONGO_CLUSTER")
        
        # URL encode credentials to handle special characters
        username_encoded = quote_plus(username)
        password_encoded = quote_plus(password)
        
        mongo_url = f"mongodb+srv://{username_encoded}:{password_encoded}@{cluster}/?retryWrites=true&w=majority"
        
        self.client = AsyncIOMotorClient(
            mongo_url,
            tls=True,
            serverSelectionTimeoutMS=10000,
        )
        
        await self.client.admin.command('ping')
        self.db = self.client[os.environ.get('DB_NAME', 'codesync')]
        return True
        
    async def _connect_local_fallback(self):
        """Fallback to local MongoDB for development"""
        if os.environ.get('ENVIRONMENT') == 'production':
            raise ValueError("Local fallback not allowed in production")
            
        mongo_url = "mongodb://localhost:27017"
        self.client = AsyncIOMotorClient(mongo_url)
        await self.client.admin.command('ping')
        self.db = self.client[os.environ.get('DB_NAME', 'codesync')]
        return True
    
    async def health_check(self):
        """Check if MongoDB connection is healthy"""
        if not self.connected or not self.client:
            return False
            
        try:
            await self.client.admin.command('ping', maxTimeMS=5000)
            return True
        except Exception as e:
            logger.error(f"MongoDB health check failed: {e}")
            self.connected = False
            return False
    
    def get_database(self):
        """Get database instance"""
        if not self.connected:
            raise RuntimeError("Database not connected. Call connect() first.")
        return self.db

# Global MongoDB instance
mongo_config = MongoDBConfig()