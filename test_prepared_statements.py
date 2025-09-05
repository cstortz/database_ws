#!/usr/bin/env python3
"""
Test script to verify prepared statements are working correctly
"""

import asyncio
import asyncpg
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_prepared_statements():
    """Test prepared statements functionality"""
    
    # Database connection parameters (adjust as needed)
    DATABASE_URL = "postgresql://user:password@localhost:5432/testdb"
    
    try:
        # Connect to database
        conn = await asyncpg.connect(DATABASE_URL)
        logger.info("Connected to database")
        
        # Create a test table
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS test_prepared (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(255),
                age INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        logger.info("Test table created/verified")
        
        # Test 1: Basic prepared statement
        logger.info("Test 1: Basic prepared statement")
        stmt = await conn.prepare("SELECT * FROM test_prepared WHERE id = $1")
        result = await stmt.fetchrow(1)
        logger.info(f"Result: {result}")
        
        # Test 2: Insert with prepared statement
        logger.info("Test 2: Insert with prepared statement")
        insert_stmt = await conn.prepare("""
            INSERT INTO test_prepared (name, email, age) 
            VALUES ($1, $2, $3) 
            RETURNING *
        """)
        
        # Insert multiple records
        test_data = [
            ("John Doe", "john@example.com", 30),
            ("Jane Smith", "jane@example.com", 25),
            ("Bob Johnson", "bob@example.com", 35)
        ]
        
        for name, email, age in test_data:
            result = await insert_stmt.fetchrow(name, email, age)
            logger.info(f"Inserted: {result}")
        
        # Test 3: Select with parameters
        logger.info("Test 3: Select with parameters")
        select_stmt = await conn.prepare("""
            SELECT * FROM test_prepared 
            WHERE age > $1 AND name ILIKE $2 
            ORDER BY age DESC
        """)
        
        results = await select_stmt.fetch(25, "%john%")
        logger.info(f"Found {len(results)} records matching criteria")
        for row in results:
            logger.info(f"  {row}")
        
        # Test 4: Update with prepared statement
        logger.info("Test 4: Update with prepared statement")
        update_stmt = await conn.prepare("""
            UPDATE test_prepared 
            SET age = $2, email = $3 
            WHERE id = $1 
            RETURNING *
        """)
        
        result = await update_stmt.fetchrow(1, 31, "john.updated@example.com")
        logger.info(f"Updated: {result}")
        
        # Test 5: Delete with prepared statement
        logger.info("Test 5: Delete with prepared statement")
        delete_stmt = await conn.prepare("""
            DELETE FROM test_prepared 
            WHERE id = $1 
            RETURNING *
        """)
        
        result = await delete_stmt.fetchrow(3)
        logger.info(f"Deleted: {result}")
        
        # Test 6: Count with prepared statement
        logger.info("Test 6: Count with prepared statement")
        count_stmt = await conn.prepare("SELECT COUNT(*) FROM test_prepared WHERE age > $1")
        count = await count_stmt.fetchval(25)
        logger.info(f"Count of records with age > 25: {count}")
        
        # Clean up
        await conn.execute("DROP TABLE IF EXISTS test_prepared")
        logger.info("Test table cleaned up")
        
        await conn.close()
        logger.info("Database connection closed")
        
        logger.info("All prepared statement tests passed!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise

async def test_database_manager():
    """Test the DatabaseManager class"""
    try:
        from app.core.database import db_manager, PreparedStatement
        
        logger.info("Testing DatabaseManager class...")
        
        # Test prepared statement creation
        stmt = db_manager.prepare_select_query(
            schema_name="public",
            table_name="test_table",
            limit=10,
            offset=0
        )
        logger.info(f"Created SELECT statement: {stmt.sql}")
        logger.info(f"Parameters: {stmt.parameters}")
        
        # Test INSERT statement
        data = {"name": "test", "email": "test@example.com"}
        insert_stmt = db_manager.prepare_insert_query("public", "test_table", data)
        logger.info(f"Created INSERT statement: {insert_stmt.sql}")
        logger.info(f"Parameters: {insert_stmt.parameters}")
        
        # Test UPDATE statement
        update_stmt = db_manager.prepare_update_query("public", "test_table", 1, data)
        logger.info(f"Created UPDATE statement: {update_stmt.sql}")
        logger.info(f"Parameters: {update_stmt.parameters}")
        
        # Test DELETE statement
        delete_stmt = db_manager.prepare_delete_query("public", "test_table", 1)
        logger.info(f"Created DELETE statement: {delete_stmt.sql}")
        logger.info(f"Parameters: {delete_stmt.parameters}")
        
        logger.info("DatabaseManager tests passed!")
        
    except Exception as e:
        logger.error(f"DatabaseManager test failed: {e}")
        raise

if __name__ == "__main__":
    # Run tests
    asyncio.run(test_prepared_statements())
    asyncio.run(test_database_manager())
