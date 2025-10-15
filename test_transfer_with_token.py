#!/usr/bin/env python3
"""
Test transfer with the fixed token_id
"""

import requests
import json

BASE_URL = "http://localhost:5001/api"

def test_transfer_with_token_id():
    # Login as user
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
    
    # Create transfer for land 14 with token_id 8
    print("🚀 Creating transfer for land 14 (token_id: 8)...")
    transfer_data = {
        "to_user": "test_receiver",
        "price": 350000,
        "transfer_type": "sale"
    }
    
    response = requests.post(
        f"{BASE_URL}/lands/14/transfer/initiate",
        headers=headers,
        json=transfer_data
    )
    
    if response.status_code == 201:
        transfer = response.json()['transfer']
        print(f"✅ Transfer created: ID {transfer['id']}")
        
        # Execute transfer
        print("⚡ Executing transfer...")
        response = requests.post(
            f"{BASE_URL}/lands/14/transfer/{transfer['id']}/execute",
            headers=headers
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("🎉 TRANSFER SUCCESSFUL!")
            print(f"   Transaction hash: {result.get('transaction_hash')}")
        else:
            print(f"❌ Transfer failed: {json.dumps(response.json(), indent=2)}")
    else:
        print(f"❌ Transfer creation failed: {response.text}")

if __name__ == "__main__":
    test_transfer_with_token_id()