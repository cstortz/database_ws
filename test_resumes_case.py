#!/usr/bin/env python3
"""
Test the specific resumes.prompt case
"""

import asyncio
import aiohttp
import json

async def test_resumes_case():
    """Test the specific case mentioned by the user"""
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Resumes Case...")
    
    # The specific case mentioned by the user
    test_case = {
        "name": "Resumes prompt query with empty parameters",
        "sql": "select * from resumes.prompt",
        "parameters": {
            "additionalProp1": {}
        }
    }
    
    print(f"📝 Testing: {test_case['name']}")
    print(f"SQL: {test_case['sql']}")
    print(f"Parameters: {test_case['parameters']}")
    
    try:
        async with aiohttp.ClientSession() as session:
            data = {
                "sql": test_case['sql'],
                "parameters": test_case['parameters']
            }
            
            async with session.post(f"{base_url}/crud/raw-sql", json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Success: {result.get('message', 'No message')}")
                    print(f"📊 Rows returned: {result.get('row_count', 0)}")
                else:
                    error_text = await response.text()
                    print(f"❌ Error ({response.status}): {error_text}")
                    
    except Exception as e:
        print(f"❌ Error testing SQL: {e}")

if __name__ == "__main__":
    asyncio.run(test_resumes_case())
