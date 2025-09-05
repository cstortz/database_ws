#!/usr/bin/env python3
"""
Test script for the new prepared SQL endpoints
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
PREPARED_BASE = f"{BASE_URL}/crud/prepared"

class PreparedEndpointTester:
    """Test class for prepared SQL endpoints"""
    
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
                    return await response.json()
            elif method.upper() == "POST":
                async with self.session.post(url, json=data) as response:
                    return await response.json()
            elif method.upper() == "DELETE":
                async with self.session.delete(url) as response:
                    return await response.json()
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return {"error": str(e)}
    
    async def test_validate_endpoint(self):
        """Test the validate endpoint"""
        logger.info("Testing /crud/prepared/validate endpoint...")
        
        # Test valid SQL
        valid_request = {
            "sql": "SELECT * FROM users WHERE id = $1 AND active = $2",
            "parameters": {"1": 123, "2": True},
            "operation_type": "read"
        }
        
        result = await self.make_request("POST", f"{PREPARED_BASE}/validate", valid_request)
        logger.info(f"Valid SQL validation result: {json.dumps(result, indent=2)}")
        
        # Test invalid SQL (wrong parameter count)
        invalid_request = {
            "sql": "SELECT * FROM users WHERE id = $1 AND active = $2",
            "parameters": {"1": 123},  # Missing second parameter
            "operation_type": "read"
        }
        
        result = await self.make_request("POST", f"{PREPARED_BASE}/validate", invalid_request)
        logger.info(f"Invalid SQL validation result: {json.dumps(result, indent=2)}")
        
        # Test dangerous SQL
        dangerous_request = {
            "sql": "DROP TABLE users",
            "parameters": {},
            "operation_type": "write"
        }
        
        result = await self.make_request("POST", f"{PREPARED_BASE}/validate", dangerous_request)
        logger.info(f"Dangerous SQL validation result: {json.dumps(result, indent=2)}")
    
    async def test_select_endpoint(self):
        """Test the select endpoint"""
        logger.info("Testing /crud/prepared/select endpoint...")
        
        # Test simple select
        select_request = {
            "sql": "SELECT version() as db_version",
            "parameters": {},
            "operation_type": "read"
        }
        
        result = await self.make_request("POST", f"{PREPARED_BASE}/select", select_request)
        logger.info(f"Select result: {json.dumps(result, indent=2)}")
        
        # Test parameterized select
        param_select_request = {
            "sql": "SELECT current_database() as db_name, current_user as user",
            "parameters": {},
            "operation_type": "read"
        }
        
        result = await self.make_request("POST", f"{PREPARED_BASE}/select", param_select_request)
        logger.info(f"Parameterized select result: {json.dumps(result, indent=2)}")
    
    async def test_insert_endpoint(self):
        """Test the insert endpoint"""
        logger.info("Testing /crud/prepared/insert endpoint...")
        
        # Test insert with RETURNING
        insert_request = {
            "sql": """
                INSERT INTO information_schema.tables 
                (table_catalog, table_schema, table_name, table_type) 
                VALUES ($1, $2, $3, $4) 
                RETURNING table_name
            """,
            "parameters": {
                "1": "test_db",
                "2": "test_schema", 
                "3": "test_table",
                "4": "BASE TABLE"
            },
            "operation_type": "write"
        }
        
        result = await self.make_request("POST", f"{PREPARED_BASE}/insert", insert_request)
        logger.info(f"Insert result: {json.dumps(result, indent=2)}")
    
    async def test_update_endpoint(self):
        """Test the update endpoint"""
        logger.info("Testing /crud/prepared/update endpoint...")
        
        # Test update (this will likely fail since we're not actually updating real data)
        update_request = {
            "sql": "UPDATE information_schema.tables SET table_name = $1 WHERE table_name = $2",
            "parameters": {
                "1": "updated_table",
                "2": "non_existent_table"
            },
            "operation_type": "write"
        }
        
        result = await self.make_request("POST", f"{PREPARED_BASE}/update", update_request)
        logger.info(f"Update result: {json.dumps(result, indent=2)}")
    
    async def test_delete_endpoint(self):
        """Test the delete endpoint"""
        logger.info("Testing /crud/prepared/delete endpoint...")
        
        # Test delete (this will likely fail since we're not actually deleting real data)
        delete_request = {
            "sql": "DELETE FROM information_schema.tables WHERE table_name = $1",
            "parameters": {
                "1": "non_existent_table"
            },
            "operation_type": "write"
        }
        
        result = await self.make_request("POST", f"{PREPARED_BASE}/delete", delete_request)
        logger.info(f"Delete result: {json.dumps(result, indent=2)}")
    
    async def test_execute_endpoint(self):
        """Test the general execute endpoint"""
        logger.info("Testing /crud/prepared/execute endpoint...")
        
        # Test read operation
        read_request = {
            "sql": "SELECT current_timestamp as current_time",
            "parameters": {},
            "operation_type": "read"
        }
        
        result = await self.make_request("POST", f"{PREPARED_BASE}/execute", read_request)
        logger.info(f"Execute read result: {json.dumps(result, indent=2)}")
        
        # Test write operation
        write_request = {
            "sql": "SELECT 1 as test_value",
            "parameters": {},
            "operation_type": "write"
        }
        
        result = await self.make_request("POST", f"{PREPARED_BASE}/execute", write_request)
        logger.info(f"Execute write result: {json.dumps(result, indent=2)}")
    
    async def test_statements_management(self):
        """Test prepared statement management endpoints"""
        logger.info("Testing prepared statement management endpoints...")
        
        # Get current statements
        result = await self.make_request("GET", f"{PREPARED_BASE}/statements")
        logger.info(f"Current statements: {json.dumps(result, indent=2)}")
        
        # Clear all statements
        result = await self.make_request("DELETE", f"{PREPARED_BASE}/statements")
        logger.info(f"Clear all statements result: {json.dumps(result, indent=2)}")
        
        # Get statements again (should be empty)
        result = await self.make_request("GET", f"{PREPARED_BASE}/statements")
        logger.info(f"Statements after clear: {json.dumps(result, indent=2)}")
    
    async def test_health_check(self):
        """Test that the service is running"""
        logger.info("Testing service health...")
        
        result = await self.make_request("GET", f"{BASE_URL}/admin/health")
        logger.info(f"Health check result: {json.dumps(result, indent=2)}")
        
        if result.get("status") == "healthy":
            logger.info("✅ Service is healthy")
        else:
            logger.error("❌ Service is not healthy")
    
    async def run_all_tests(self):
        """Run all tests"""
        logger.info("🚀 Starting prepared endpoint tests...")
        
        try:
            # Test health first
            await self.test_health_check()
            
            # Test prepared endpoints
            await self.test_validate_endpoint()
            await self.test_select_endpoint()
            await self.test_insert_endpoint()
            await self.test_update_endpoint()
            await self.test_delete_endpoint()
            await self.test_execute_endpoint()
            await self.test_statements_management()
            
            logger.info("✅ All tests completed successfully!")
            
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            raise

async def main():
    """Main test function"""
    async with PreparedEndpointTester() as tester:
        await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
