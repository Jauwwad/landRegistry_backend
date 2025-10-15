#!/usr/bin/env python3
"""
Cancel existing transfer and create new one
"""

import requests
import json

BASE_URL = "http://localhost:5001/api"

def cancel_and_test_transfer():
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
    
    # Cancel transfer 7 for land 14
    print("❌ Cancelling existing transfer...")
    response = requests.post(
        f"{BASE_URL}/lands/14/transfer/7/cancel",
        headers=headers
    )
    
    if response.status_code == 200:
        print("✅ Transfer cancelled")
    else:
        print(f"⚠️ Cancel failed: {response.text}")
    
    # Create new transfer
    print("🚀 Creating new transfer...")
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
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
    else:
        print(f"❌ Transfer creation failed: {response.text}")

if __name__ == "__main__":
    cancel_and_test_transfer()