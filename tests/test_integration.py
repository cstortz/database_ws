"""
Comprehensive integration tests for the Database Service API

This test suite provides end-to-end testing of all endpoints and functionality,
including complex workflows and edge cases.
"""

import pytest
import asyncio
import json
from httpx import AsyncClient
from app.main import app
from app.core.database import test_connection, get_pool_stats, close_pool
from app.core.config import settings

@pytest.fixture
async def client():
    """Async client for testing"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture(autouse=True)
async def cleanup():
    """Cleanup after tests"""
    yield
    await close_pool()

class TestServiceIntegration:
    """Test complete service integration and workflows"""
    
    @pytest.mark.asyncio
    async def test_service_startup_and_health(self, client):
        """Test complete service startup and health check workflow"""
        # Test root endpoint
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "2.1.0"
        assert "features" in data
        
        # Test basic health
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        
        # Test detailed admin health
        response = await client.get("/admin/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
    
    @pytest.mark.asyncio
    async def test_database_metadata_workflow(self, client):
        """Test complete database metadata exploration workflow"""
        # Get database info
        response = await client.get("/admin/db-info")
        assert response.status_code == 200
        db_info = response.json()
        assert "version" in db_info
        assert "database" in db_info
        
        # Get all databases
        response = await client.get("/admin/databases")
        assert response.status_code == 200
        databases = response.json()
        assert "databases" in databases
        
        # Get all schemas
        response = await client.get("/admin/schemas")
        assert response.status_code == 200
        schemas = response.json()
        assert "schemas" in schemas
        
        # Get all tables
        response = await client.get("/admin/tables")
        assert response.status_code == 200
        tables = response.json()
        assert "tables" in tables
        
        # Get tables by schema
        response = await client.get("/admin/tables/public")
        assert response.status_code == 200
        schema_tables = response.json()
        assert "tables" in schema_tables

class TestCRUDWorkflow:
    """Test complete CRUD workflow scenarios"""
    
    @pytest.mark.asyncio
    async def test_complete_crud_workflow(self, client):
        """Test complete CRUD workflow: Create -> Read -> Update -> Delete"""
        # 1. Create a record
        create_data = {
            "data": {
                "content": "Integration test document"
            }
        }
        
        response = await client.post("/crud/public/documents", json=create_data)
        assert response.status_code == 200
        created_record = response.json()
        record_id = created_record["id"]
        assert created_record["data"]["content"] == "Integration test document"
        
        # 2. Read the created record
        response = await client.get(f"/crud/public/documents/{record_id}")
        assert response.status_code == 200
        read_record = response.json()
        assert read_record["id"] == record_id
        assert read_record["data"]["content"] == "Integration test document"
        
        # 3. Update the record
        update_data = {
            "data": {
                "content": "Updated integration test document"
            }
        }
        
        response = await client.put(f"/crud/public/documents/{record_id}", json=update_data)
        assert response.status_code == 200
        updated_record = response.json()
        assert updated_record["data"]["content"] == "Updated integration test document"
        
        # 4. Verify the update
        response = await client.get(f"/crud/public/documents/{record_id}")
        assert response.status_code == 200
        verify_record = response.json()
        assert verify_record["data"]["content"] == "Updated integration test document"
        
        # 5. Delete the record
        response = await client.delete(f"/crud/public/documents/{record_id}")
        assert response.status_code == 200
        delete_result = response.json()
        assert "message" in delete_result
        assert "deleted_record" in delete_result
        
        # 6. Verify deletion
        response = await client.get(f"/crud/public/documents/{record_id}")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_crud_pagination_and_ordering(self, client):
        """Test CRUD operations with pagination and ordering"""
        # Create multiple test records
        for i in range(3):
            create_data = {
                "data": {
                    "content": f"Pagination test document {i}"
                }
            }
            response = await client.post("/crud/public/documents", json=create_data)
            assert response.status_code == 200
        
        # Test pagination
        response = await client.get("/crud/public/documents?limit=2&offset=0")
        assert response.status_code == 200
        data = response.json()
        assert len(data["records"]) <= 2
        assert "count" in data
        assert "total_count" in data
        
        # Test ordering
        response = await client.get("/crud/public/documents?limit=5&order_by=id DESC")
        assert response.status_code == 200
        data = response.json()
        assert "records" in data
        
        # Clean up test records
        for record in data["records"]:
            if "Pagination test document" in record["data"]["content"]:
                response = await client.delete(f"/crud/public/documents/{record['id']}")
                assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_upsert_workflow(self, client):
        """Test upsert (create or update) workflow"""
        # Test upsert with new ID
        upsert_data = {
            "data": {
                "content": "Upsert test document"
            }
        }
        
        response = await client.patch("/crud/public/documents/8888", json=upsert_data)
        assert response.status_code == 200
        upsert_result = response.json()
        assert upsert_result["operation"] == "created"
        assert upsert_result["record"]["data"]["content"] == "Upsert test document"
        
        # Test upsert with existing ID (update)
        upsert_data["data"]["content"] = "Updated upsert test document"
        response = await client.patch("/crud/public/documents/8888", json=upsert_data)
        assert response.status_code == 200
        upsert_result = response.json()
        assert upsert_result["operation"] == "updated"
        assert upsert_result["record"]["data"]["content"] == "Updated upsert test document"
        
        # Clean up
        response = await client.delete("/crud/public/documents/8888")
        assert response.status_code == 200

class TestSQLOperationsWorkflow:
    """Test SQL operations workflow scenarios"""
    
    @pytest.mark.asyncio
    async def test_raw_sql_workflow(self, client):
        """Test raw SQL operations workflow"""
        # Test read operation
        sql_data = {
            "sql": "SELECT COUNT(*) as total FROM documents",
            "parameters": {}
        }
        
        response = await client.post("/raw/sql", json=sql_data)
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "data" in data
        assert isinstance(data["data"], list)
        
        # Test write operation
        sql_data = {
            "sql": "CREATE TEMP TABLE IF NOT EXISTS integration_test (id TEXT, name TEXT)",
            "parameters": {}
        }
        
        response = await client.post("/raw/sql/write", json=sql_data)
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
    
    @pytest.mark.asyncio
    async def test_prepared_sql_workflow(self, client):
        """Test prepared SQL operations workflow"""
        # Test validation
        sql_data = {
            "sql": "SELECT * FROM documents WHERE id = $1",
            "parameters": {"1": "1"},
            "operation_type": "read"
        }
        
        response = await client.post("/crud/prepared/validate", json=sql_data)
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == True
        
        # Test select operation
        sql_data = {
            "sql": "SELECT COUNT(*) as total FROM documents",
            "parameters": {},
            "operation_type": "read"
        }
        
        response = await client.post("/crud/prepared/select", json=sql_data)
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "data" in data
        
        # Test statements listing
        response = await client.get("/crud/prepared/statements")
        assert response.status_code == 200
        data = response.json()
        assert "statements" in data
        assert isinstance(data["statements"], list)

class TestErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest.mark.asyncio
    async def test_invalid_endpoints(self, client):
        """Test invalid endpoint handling"""
        # Test non-existent table
        response = await client.get("/crud/public/non_existent_table")
        assert response.status_code == 404
        
        # Test invalid schema
        response = await client.get("/crud/invalid_schema/documents")
        assert response.status_code == 404
        
        # Test invalid record ID
        response = await client.get("/crud/public/documents/999999")
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_invalid_sql_operations(self, client):
        """Test invalid SQL operation handling"""
        # Test invalid SQL
        sql_data = {
            "sql": "INVALID SQL STATEMENT",
            "parameters": {}
        }
        
        response = await client.post("/raw/sql", json=sql_data)
        assert response.status_code == 400
        
        # Test SQL injection attempt
        sql_data = {
            "sql": "SELECT * FROM documents; DROP TABLE documents;",
            "parameters": {}
        }
        
        response = await client.post("/raw/sql", json=sql_data)
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_invalid_parameters(self, client):
        """Test invalid parameter handling"""
        # Test missing required fields
        response = await client.post("/crud/public/documents", json={})
        assert response.status_code == 422
        
        # Test invalid JSON
        response = await client.post("/crud/public/documents", 
                                   content="invalid json",
                                   headers={"Content-Type": "application/json"})
        assert response.status_code == 422

class TestPerformanceAndConcurrency:
    """Test performance and concurrency scenarios"""
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, client):
        """Test handling of concurrent requests"""
        # Create multiple concurrent requests
        tasks = []
        for i in range(5):
            task = client.get("/admin/health")
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        
        # All requests should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_connection_pool_handling(self, client):
        """Test connection pool handling"""
        # Make multiple requests to test connection pool
        for i in range(10):
            response = await client.get("/admin/health")
            assert response.status_code == 200
        
        # Test pool stats
        stats = await get_pool_stats()
        assert stats["pool_created"] == True
        assert stats["total_connections"] > 0

class TestSecurityFeatures:
    """Test security features and validation"""
    
    @pytest.mark.asyncio
    async def test_sql_injection_protection(self, client):
        """Test SQL injection protection"""
        # Test various SQL injection attempts
        injection_attempts = [
            "'; DROP TABLE documents; --",
            "1' OR '1'='1",
            "1; INSERT INTO documents (content) VALUES ('hacked');",
            "1' UNION SELECT * FROM documents --"
        ]
        
        for injection in injection_attempts:
            sql_data = {
                "sql": f"SELECT * FROM documents WHERE content = '{injection}'",
                "parameters": {}
            }
            
            response = await client.post("/raw/sql", json=sql_data)
            # Should either succeed safely (no results) or fail with validation error
            assert response.status_code in [200, 400]
    
    @pytest.mark.asyncio
    async def test_parameter_validation(self, client):
        """Test parameter validation"""
        # Test with valid parameters
        sql_data = {
            "sql": "SELECT * FROM documents WHERE id = $1",
            "parameters": {"1": "1"}
        }
        
        response = await client.post("/raw/sql", json=sql_data)
        assert response.status_code == 200
        
        # Test with missing parameters
        sql_data = {
            "sql": "SELECT * FROM documents WHERE id = $1",
            "parameters": {}
        }
        
        response = await client.post("/raw/sql", json=sql_data)
        assert response.status_code == 400

if __name__ == "__main__":
    # Run tests manually
    pytest.main([__file__, "-v"])
