#!/usr/bin/env python3
"""
Test script for Raw SQL endpoints
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
RAW_BASE = f"{BASE_URL}/raw"

class RawEndpointTester:
    """Test class for raw SQL endpoints"""
    
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
    
    async def test_health_check(self):
        """Test that the service is running"""
        logger.info("🔍 Testing service health...")
        
        result = await self.make_request("GET", f"{BASE_URL}/admin/health")
        logger.info(f"Health check result: {json.dumps(result, indent=2)}")
        
        if result.get("status") == "healthy":
            logger.info("✅ Service is healthy")
        else:
            logger.error("❌ Service is not healthy")
        return result
    
    async def test_raw_sql_simple(self):
        """Test simple raw SQL read operations"""
        logger.info("🔍 Testing /raw/sql endpoint - Simple queries...")
        
        # Test 1: Simple SELECT without parameters
        simple_request = {
            "sql": "SELECT version() as db_version, current_database() as db_name, current_user as user"
        }
        
        result = await self.make_request("POST", f"{RAW_BASE}/sql", simple_request)
        logger.info(f"Simple SQL result: {json.dumps(result, indent=2)}")
        
        if "error" not in result and result.get("success"):
            logger.info("✅ Simple SQL query successful")
        else:
            logger.error("❌ Simple SQL query failed")
        
        return result
    
    async def test_raw_sql_with_parameters(self):
        """Test raw SQL with parameters"""
        logger.info("🔍 Testing /raw/sql endpoint - Parameterized queries...")
        
        # Test 2: SELECT with parameters
        param_request = {
            "sql": "SELECT $1 as test_param, $2 as another_param, current_timestamp as current_time",
            "parameters": {
                "1": "Hello World",
                "2": "42"
            }
        }
        
        result = await self.make_request("POST", f"{RAW_BASE}/sql", param_request)
        logger.info(f"Parameterized SQL result: {json.dumps(result, indent=2)}")
        
        if "error" not in result and result.get("success"):
            logger.info("✅ Parameterized SQL query successful")
        else:
            logger.error("❌ Parameterized SQL query failed")
        
        return result
    
    async def test_raw_sql_database_info(self):
        """Test raw SQL to get database information"""
        logger.info("🔍 Testing /raw/sql endpoint - Database information queries...")
        
        # Test 3: Get database schema information
        schema_request = {
            "sql": """
                SELECT 
                    schemaname,
                    tablename,
                    tableowner,
                    hasindexes,
                    hasrules,
                    hastriggers
                FROM pg_tables 
                WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
                ORDER BY schemaname, tablename
                LIMIT 10
            """
        }
        
        result = await self.make_request("POST", f"{RAW_BASE}/sql", schema_request)
        logger.info(f"Schema info result: {json.dumps(result, indent=2)}")
        
        if "error" not in result and result.get("success"):
            logger.info("✅ Schema info query successful")
        else:
            logger.error("❌ Schema info query failed")
        
        return result
    
    async def test_raw_sql_error_handling(self):
        """Test raw SQL error handling"""
        logger.info("🔍 Testing /raw/sql endpoint - Error handling...")
        
        # Test 4: Invalid SQL
        invalid_request = {
            "sql": "SELECT * FROM non_existent_table_12345"
        }
        
        result = await self.make_request("POST", f"{RAW_BASE}/sql", invalid_request)
        logger.info(f"Invalid SQL result: {json.dumps(result, indent=2)}")
        
        if "error" in result:
            logger.info("✅ Error handling working correctly")
        else:
            logger.error("❌ Error handling failed")
        
        return result
    
    async def test_raw_sql_write_simple(self):
        """Test simple raw SQL write operations"""
        logger.info("🔍 Testing /raw/sql/write endpoint - Simple write operations...")
        
        # Test 5: Simple write operation (CREATE TEMP TABLE with IF NOT EXISTS)
        write_request = {
            "sql": "CREATE TEMP TABLE IF NOT EXISTS test_write_table_v2 (id TEXT, name TEXT)"
        }
        
        result = await self.make_request("POST", f"{RAW_BASE}/sql/write", write_request)
        logger.info(f"Simple write result: {json.dumps(result, indent=2)}")
        
        if "error" not in result and result.get("success"):
            logger.info("✅ Simple write operation successful")
        else:
            logger.error("❌ Simple write operation failed")
        
        return result
    
    async def test_raw_sql_write_with_parameters(self):
        """Test raw SQL write operations with parameters"""
        logger.info("🔍 Testing /raw/sql/write endpoint - Parameterized write operations...")
        
        # Test 6: Write operation with parameters (INSERT into temp table)
        param_write_request = {
            "sql": "INSERT INTO test_write_table_v2 (id, name) VALUES ($1, $2)",
            "parameters": {
                "1": "1",
                "2": "test_value"
            }
        }
        
        result = await self.make_request("POST", f"{RAW_BASE}/sql/write", param_write_request)
        logger.info(f"Parameterized write result: {json.dumps(result, indent=2)}")
        
        if "error" not in result and result.get("success"):
            logger.info("✅ Parameterized write operation successful")
        else:
            logger.error("❌ Parameterized write operation failed")
        
        return result
    
    async def test_raw_sql_write_error_handling(self):
        """Test raw SQL write error handling"""
        logger.info("🔍 Testing /raw/sql/write endpoint - Error handling...")
        
        # Test 7: Invalid write operation
        invalid_write_request = {
            "sql": "INSERT INTO non_existent_table (id, name) VALUES (1, 'test')"
        }
        
        result = await self.make_request("POST", f"{RAW_BASE}/sql/write", invalid_write_request)
        logger.info(f"Invalid write result: {json.dumps(result, indent=2)}")
        
        if "error" in result:
            logger.info("✅ Write error handling working correctly")
        else:
            logger.error("❌ Write error handling failed")
        
        return result
    
    async def test_raw_sql_security(self):
        """Test raw SQL security features"""
        logger.info("🔍 Testing /raw/sql endpoint - Security features...")
        
        # Test 8: Test SQL injection protection
        injection_request = {
            "sql": "SELECT * FROM users WHERE id = 1; DROP TABLE users; --"
        }
        
        result = await self.make_request("POST", f"{RAW_BASE}/sql", injection_request)
        logger.info(f"SQL injection test result: {json.dumps(result, indent=2)}")
        
        if "error" in result and "injection" in str(result).lower():
            logger.info("✅ SQL injection protection working")
        else:
            logger.warning("⚠️ SQL injection protection may need review")
        
        return result
    
    async def run_all_raw_tests(self):
        """Run all raw SQL endpoint tests"""
        logger.info("🚀 Starting Raw SQL endpoint tests...")
        
        try:
            # Test health first
            await self.test_health_check()
            
            # Test raw SQL read operations
            await self.test_raw_sql_simple()
            await self.test_raw_sql_with_parameters()
            await self.test_raw_sql_database_info()
            await self.test_raw_sql_error_handling()
            await self.test_raw_sql_security()
            
            # Test raw SQL write operations
            await self.test_raw_sql_write_simple()
            await self.test_raw_sql_write_with_parameters()
            await self.test_raw_sql_write_error_handling()
            
            logger.info("✅ All raw SQL endpoint tests completed!")
            
        except Exception as e:
            logger.error(f"❌ Raw SQL test failed: {e}")
            raise

async def main():
    """Main test function"""
    async with RawEndpointTester() as tester:
        await tester.run_all_raw_tests()

if __name__ == "__main__":
    asyncio.run(main())
