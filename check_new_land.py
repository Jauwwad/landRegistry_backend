#!/usr/bin/env python3
"""
Check the status of the newly created land
"""

import requests
import json

BASE_URL = "http://localhost:5001/api"

def check_land_status():
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
    
    # Get the latest land (ID 14)
    response = requests.get(f"{BASE_URL}/lands/14", headers=headers)
    
    if response.status_code == 200:
        land_data = response.json()
        print("🏢 Raw Land Response:")
        print(json.dumps(land_data, indent=2))
        
        land = land_data.get('land', land_data)  # Handle different response formats
        print(f"\n🏢 Land Status:")
        print(f"   ID: {land.get('id', 'N/A')}")
        print(f"   Title: {land.get('title', 'N/A')}")
        print(f"   Status: {land.get('status', 'N/A')}")
        print(f"   Registered on blockchain: {land.get('is_registered_on_blockchain', False)}")
        print(f"   Token ID: {land.get('token_id', 'None')}")
        print(f"   Blockchain TX: {land.get('blockchain_tx_hash', 'None')}")
        print(f"   Owner wallet: {land.get('wallet_address', 'None')}")
    else:
        print(f"❌ Failed to get land: {response.text}")

if __name__ == "__main__":
    check_land_status()