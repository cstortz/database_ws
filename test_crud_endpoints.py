#!/usr/bin/env python3
"""
Test script for CRUD endpoints
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
CRUD_BASE = f"{BASE_URL}/crud"

class CrudEndpointTester:
    """Test class for CRUD endpoints"""
    
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
            elif method.upper() == "PUT":
                async with self.session.put(url, json=data) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {
                            "error": f"HTTP {response.status}",
                            "detail": await response.text()
                        }
            elif method.upper() == "DELETE":
                async with self.session.delete(url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {
                            "error": f"HTTP {response.status}",
                            "detail": await response.text()
                        }
            elif method.upper() == "PATCH":
                async with self.session.patch(url, json=data) as response:
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
    
    async def test_crud_read_multiple(self):
        """Test reading multiple records from a table"""
        logger.info("🔍 Testing GET /crud/{schema}/{table} - Read multiple records...")
        
        # Test reading from public.documents table
        result = await self.make_request("GET", f"{CRUD_BASE}/public/documents?limit=5")
        logger.info(f"Read multiple records result: {json.dumps(result, indent=2)}")
        
        if "error" not in result and result.get("records") is not None:
            logger.info("✅ Read multiple records successful")
        else:
            logger.error("❌ Read multiple records failed")
        
        return result
    
    async def test_crud_read_single(self):
        """Test reading a single record by ID"""
        logger.info("🔍 Testing GET /crud/{schema}/{table}/{id} - Read single record...")
        
        # First, get a record ID from the documents table
        records_result = await self.make_request("GET", f"{CRUD_BASE}/public/documents?limit=1")
        
        if "error" not in records_result and records_result.get("records"):
            record_id = records_result["records"][0].get("id")
            if record_id:
                result = await self.make_request("GET", f"{CRUD_BASE}/public/documents/{record_id}")
                logger.info(f"Read single record result: {json.dumps(result, indent=2)}")
                
                if "error" not in result and result.get("data"):
                    logger.info("✅ Read single record successful")
                else:
                    logger.error("❌ Read single record failed")
            else:
                logger.warning("⚠️ No records found to test single read")
                result = {"warning": "No records found"}
        else:
            logger.warning("⚠️ Could not get records for single read test")
            result = {"warning": "Could not get records"}
        
        return result
    
    async def test_crud_create(self):
        """Test creating a new record"""
        logger.info("🔍 Testing POST /crud/{schema}/{table} - Create record...")
        
        # Test creating a record in the documents table
        create_data = {
            "data": {
                "content": "This is a test document created by the CRUD test script"
            }
        }
        
        result = await self.make_request("POST", f"{CRUD_BASE}/public/documents", create_data)
        logger.info(f"Create record result: {json.dumps(result, indent=2)}")
        
        if "error" not in result and result.get("data"):
            logger.info("✅ Create record successful")
        else:
            logger.error("❌ Create record failed")
        
        return result
    
    async def test_crud_update(self):
        """Test updating an existing record"""
        logger.info("🔍 Testing PUT /crud/{schema}/{table}/{id} - Update record...")
        
        # First, get a record ID from the documents table
        records_result = await self.make_request("GET", f"{CRUD_BASE}/public/documents?limit=1")
        
        if "error" not in records_result and records_result.get("records"):
            record_id = records_result["records"][0].get("id")
            if record_id:
                update_data = {
                    "data": {
                        "content": "This document has been updated by the CRUD test script"
                    }
                }
                
                result = await self.make_request("PUT", f"{CRUD_BASE}/public/documents/{record_id}", update_data)
                logger.info(f"Update record result: {json.dumps(result, indent=2)}")
                
                if "error" not in result and result.get("data"):
                    logger.info("✅ Update record successful")
                else:
                    logger.error("❌ Update record failed")
            else:
                logger.warning("⚠️ No records found to test update")
                result = {"warning": "No records found"}
        else:
            logger.warning("⚠️ Could not get records for update test")
            result = {"warning": "Could not get records"}
        
        return result
    
    async def test_crud_delete(self):
        """Test deleting a record"""
        logger.info("🔍 Testing DELETE /crud/{schema}/{table}/{id} - Delete record...")
        
        # First, create a record to delete
        create_data = {
            "data": {
                "content": "This document will be deleted by the CRUD test script"
            }
        }
        
        create_result = await self.make_request("POST", f"{CRUD_BASE}/public/documents", create_data)
        
        if "error" not in create_result and create_result.get("data"):
            record_id = create_result["data"].get("id")
            if record_id:
                result = await self.make_request("DELETE", f"{CRUD_BASE}/public/documents/{record_id}")
                logger.info(f"Delete record result: {json.dumps(result, indent=2)}")
                
                if "error" not in result and result.get("deleted_record"):
                    logger.info("✅ Delete record successful")
                else:
                    logger.error("❌ Delete record failed")
            else:
                logger.warning("⚠️ Created record has no ID")
                result = {"warning": "Created record has no ID"}
        else:
            logger.warning("⚠️ Could not create record for delete test")
            result = {"warning": "Could not create record"}
        
        return result
    
    async def test_crud_upsert(self):
        """Test upserting a record"""
        logger.info("🔍 Testing PATCH /crud/{schema}/{table}/{id} - Upsert record...")
        
        # Test upsert with a new ID
        test_id = "999"
        upsert_data = {
            "data": {
                "content": "This document was upserted by the CRUD test script"
            }
        }
        
        result = await self.make_request("PATCH", f"{CRUD_BASE}/public/documents/{test_id}", upsert_data)
        logger.info(f"Upsert record result: {json.dumps(result, indent=2)}")
        
        if "error" not in result and result.get("record"):
            logger.info("✅ Upsert record successful")
        else:
            logger.error("❌ Upsert record failed")
        
        return result
    
    async def test_crud_pagination(self):
        """Test CRUD pagination features"""
        logger.info("🔍 Testing CRUD pagination features...")
        
        # Test with limit and offset
        result = await self.make_request("GET", f"{CRUD_BASE}/public/documents?limit=2&offset=0")
        logger.info(f"Pagination test result: {json.dumps(result, indent=2)}")
        
        if "error" not in result and result.get("records") is not None:
            logger.info("✅ Pagination test successful")
        else:
            logger.error("❌ Pagination test failed")
        
        return result
    
    async def test_crud_ordering(self):
        """Test CRUD ordering features"""
        logger.info("🔍 Testing CRUD ordering features...")
        
        # Test with ordering
        result = await self.make_request("GET", f"{CRUD_BASE}/public/documents?limit=3&order_by=content DESC")
        logger.info(f"Ordering test result: {json.dumps(result, indent=2)}")
        
        if "error" not in result and result.get("records") is not None:
            logger.info("✅ Ordering test successful")
        else:
            logger.error("❌ Ordering test failed")
        
        return result
    
    async def test_crud_error_handling(self):
        """Test CRUD error handling"""
        logger.info("🔍 Testing CRUD error handling...")
        
        # Test with non-existent table
        result = await self.make_request("GET", f"{CRUD_BASE}/public/non_existent_table")
        logger.info(f"Error handling test result: {json.dumps(result, indent=2)}")
        
        if "error" in result:
            logger.info("✅ Error handling working correctly")
        else:
            logger.error("❌ Error handling failed")
        
        return result
    
    async def run_all_crud_tests(self):
        """Run all CRUD endpoint tests"""
        logger.info("🚀 Starting CRUD endpoint tests...")
        
        try:
            # Test health first
            await self.test_health_check()
            
            # Test CRUD operations
            await self.test_crud_read_multiple()
            await self.test_crud_read_single()
            await self.test_crud_create()
            await self.test_crud_update()
            await self.test_crud_delete()
            await self.test_crud_upsert()
            
            # Test CRUD features
            await self.test_crud_pagination()
            await self.test_crud_ordering()
            await self.test_crud_error_handling()
            
            logger.info("✅ All CRUD endpoint tests completed!")
            
        except Exception as e:
            logger.error(f"❌ CRUD test failed: {e}")
            raise

async def main():
    """Main test function"""
    async with CrudEndpointTester() as tester:
        await tester.run_all_crud_tests()

if __name__ == "__main__":
    asyncio.run(main())
