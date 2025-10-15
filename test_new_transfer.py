#!/usr/bin/env python3
"""
Test creating a new transfer and immediately testing execution
"""

import requests
import json
import time

BASE_URL = "http://localhost:5001/api"

def test_complete_workflow():
    # Login
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "demo_user",
        "password": "user123"
    })
    
    if response.status_code == 200:
        token = response.json()['access_token']
        print("✅ Login successful")
    else:
        print(f"❌ Login failed: {response.text}")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a new transfer
    print("🚀 Creating new transfer...")
    transfer_data = {
        "to_user": "test_receiver",
        "price": 250000,
        "transfer_type": "sale"
    }
    
    response = requests.post(
        f"{BASE_URL}/lands/7/transfer/initiate",
        headers=headers,
        json=transfer_data
    )
    
    if response.status_code == 201:
        transfer = response.json()['transfer']
        transfer_id = transfer['id']
        land_id = transfer['land_id']
        print(f"✅ Transfer created: ID {transfer_id} for land {land_id}")
        
        # Immediately try to execute
        print("⚡ Attempting to execute transfer...")
        response = requests.post(
            f"{BASE_URL}/lands/{land_id}/transfer/{transfer_id}/execute",
            headers=headers
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
    else:
        print(f"❌ Transfer creation failed: {response.text}")

if __name__ == "__main__":
    test_complete_workflow()