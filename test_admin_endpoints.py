#!/usr/bin/env python3
"""
Test script for Admin endpoints
"""

import asyncio
import aiohttp
import json
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
BASE_URL = "http://localhost:8000"
ADMIN_BASE = f"{BASE_URL}/admin"

class AdminEndpointTester:
    """Test class for admin endpoints"""
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def make_request(self, method: str, url: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make HTTP request and return response"""
        try:
            if method.upper() == "GET":
                async with self.session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {
                            "error": f"HTTP {response.status}",
                            "detail": await response.text()
                        }
            elif method.upper() == "POST":
                async with self.session.post(url, json=data) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {
                            "error": f"HTTP {response.status}",
                            "detail": await response.text()
                        }
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return {"error": str(e)}
    
    async def test_root_endpoint(self):
        """Test the root endpoint"""
        logger.info("🔍 Testing GET / (root endpoint)...")
        
        result = await self.make_request("GET", BASE_URL)
        logger.info(f"Root endpoint result: {json.dumps(result, indent=2)}")
        
        if "error" not in result:
            logger.info("✅ Root endpoint working")
        else:
            logger.error("❌ Root endpoint failed")
        return result
    
    async def test_health_endpoint(self):
        """Test the simple health endpoint"""
        logger.info("🔍 Testing GET /health (simple health check)...")
        
        result = await self.make_request("GET", f"{BASE_URL}/health")
        logger.info(f"Health endpoint result: {json.dumps(result, indent=2)}")
        
        if "error" not in result:
            logger.info("✅ Health endpoint working")
        else:
            logger.error("❌ Health endpoint failed")
        return result
    
    async def test_admin_health(self):
        """Test the admin health endpoint"""
        logger.info("🔍 Testing GET /admin/health (detailed health check)...")
        
        result = await self.make_request("GET", f"{ADMIN_BASE}/health")
        logger.info(f"Admin health result: {json.dumps(result, indent=2)}")
        
        if "error" not in result and result.get("status") == "healthy":
            logger.info("✅ Admin health check passed")
        else:
            logger.error("❌ Admin health check failed")
        return result
    
    async def test_admin_connection(self):
        """Test the admin connection test endpoint"""
        logger.info("🔍 Testing GET /admin/test-connection (connection test)...")
        
        result = await self.make_request("GET", f"{ADMIN_BASE}/test-connection")
        logger.info(f"Connection test result: {json.dumps(result, indent=2)}")
        
        if "error" not in result and result.get("status") == "success":
            logger.info("✅ Connection test passed")
        else:
            logger.error("❌ Connection test failed")
        return result
    
    async def test_admin_db_info(self):
        """Test the admin database info endpoint"""
        logger.info("🔍 Testing GET /admin/db-info (database information)...")
        
        result = await self.make_request("GET", f"{ADMIN_BASE}/db-info")
        logger.info(f"Database info result: {json.dumps(result, indent=2)}")
        
        if "error" not in result:
            logger.info("✅ Database info retrieved successfully")
        else:
            logger.error("❌ Database info failed")
        return result
    
    async def test_admin_databases(self):
        """Test the admin databases endpoint"""
        logger.info("🔍 Testing GET /admin/databases (list all databases)...")
        
        result = await self.make_request("GET", f"{ADMIN_BASE}/databases")
        logger.info(f"Databases result: {json.dumps(result, indent=2)}")
        
        if "error" not in result:
            logger.info("✅ Databases list retrieved successfully")
        else:
            logger.error("❌ Databases list failed")
        return result
    
    async def test_admin_schemas(self):
        """Test the admin schemas endpoint"""
        logger.info("🔍 Testing GET /admin/schemas (list all schemas)...")
        
        result = await self.make_request("GET", f"{ADMIN_BASE}/schemas")
        logger.info(f"Schemas result: {json.dumps(result, indent=2)}")
        
        if "error" not in result:
            logger.info("✅ Schemas list retrieved successfully")
        else:
            logger.error("❌ Schemas list failed")
        return result
    
    async def test_admin_tables(self):
        """Test the admin tables endpoint"""
        logger.info("🔍 Testing GET /admin/tables (list all tables)...")
        
        result = await self.make_request("GET", f"{ADMIN_BASE}/tables")
        logger.info(f"Tables result: {json.dumps(result, indent=2)}")
        
        if "error" not in result:
            logger.info("✅ Tables list retrieved successfully")
        else:
            logger.error("❌ Tables list failed")
        return result
    
    async def test_admin_tables_by_schema(self, schema_name: str = "public"):
        """Test the admin tables by schema endpoint"""
        logger.info(f"🔍 Testing GET /admin/tables/{schema_name} (tables in schema)...")
        
        result = await self.make_request("GET", f"{ADMIN_BASE}/tables/{schema_name}")
        logger.info(f"Tables by schema result: {json.dumps(result, indent=2)}")
        
        if "error" not in result:
            logger.info(f"✅ Tables in schema '{schema_name}' retrieved successfully")
        else:
            logger.error(f"❌ Tables in schema '{schema_name}' failed")
        return result
    
    async def run_all_admin_tests(self):
        """Run all admin endpoint tests"""
        logger.info("🚀 Starting Admin endpoint tests...")
        
        try:
            # Test basic endpoints first
            await self.test_root_endpoint()
            await self.test_health_endpoint()
            
            # Test admin endpoints
            await self.test_admin_health()
            await self.test_admin_connection()
            await self.test_admin_db_info()
            await self.test_admin_databases()
            await self.test_admin_schemas()
            await self.test_admin_tables()
            
            # Test tables by schema (try common schema names)
            for schema in ["public", "information_schema"]:
                await self.test_admin_tables_by_schema(schema)
            
            logger.info("✅ All admin endpoint tests completed!")
            
        except Exception as e:
            logger.error(f"❌ Admin test failed: {e}")
            raise

async def main():
    """Main test function"""
    async with AdminEndpointTester() as tester:
        await tester.run_all_admin_tests()

if __name__ == "__main__":
    asyncio.run(main())
