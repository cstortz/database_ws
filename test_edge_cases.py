#!/usr/bin/env python3
"""
Test edge cases for parameter handling
"""

import asyncio
import aiohttp
import json

async def test_edge_cases():
    """Test various edge cases"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Edge Cases...")
    
    # Edge cases
    test_cases = [
        {
            "name": "Empty parameters object",
            "sql": "SELECT * FROM documents",
            "parameters": {}
        },
        {
            "name": "Null parameters",
            "sql": "SELECT COUNT(*) FROM documents",
            "parameters": None
        },
        {
            "name": "Parameters with empty values",
            "sql": "SELECT * FROM documents",
            "parameters": {"prop1": "", "prop2": None, "prop3": {}}
        },
        {
            "name": "Valid parameters with placeholders",
            "sql": "SELECT * FROM documents WHERE id = $1",
            "parameters": {"id": 1}
        }
    ]
    
    try:
        async with aiohttp.ClientSession() as session:
            for test_case in test_cases:
                print(f"\n📝 Testing: {test_case['name']}")
                print(f"SQL: {test_case['sql']}")
                print(f"Parameters: {test_case['parameters']}")
                
                data = {
                    "sql": test_case['sql'],
                    "parameters": test_case['parameters']
                }
                
                async with session.post(f"{base_url}/crud/raw-sql", json=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"✅ Success: {result.get('message', 'No message')}")
                    else:
                        error_text = await response.text()
                        print(f"❌ Error ({response.status}): {error_text}")
                        
    except Exception as e:
        print(f"❌ Error testing SQL: {e}")

if __name__ == "__main__":
    asyncio.run(test_edge_cases())
