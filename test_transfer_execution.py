#!/usr/bin/env python3
"""
Test transfer execution to see the improved error handling
"""

import requests
import json

BASE_URL = "http://localhost:5001/api"

def test_transfer_execution():
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
    
    # Get the latest transfer
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/lands/transfers", headers=headers)
    
    if response.status_code == 200:
        transfers = response.json()
        print(f"Raw transfers response: {transfers}")
        
        # Handle if transfers is a list of dictionaries or a dictionary with lists
        if isinstance(transfers, list):
            transfer_list = transfers
        elif isinstance(transfers, dict) and 'transfers' in transfers:
            transfer_list = transfers['transfers']
        else:
            # Check if it's user transfers which might have different structure
            transfer_list = transfers
        
        if isinstance(transfer_list, list):
            pending_transfers = [t for t in transfer_list if isinstance(t, dict) and t.get('status') == 'pending']
        else:
            print(f"Unexpected transfer format: {type(transfer_list)}")
            return
        
        if not pending_transfers:
            print("❌ No pending transfers found")
            return
        
        transfer = pending_transfers[0]
        transfer_id = transfer['id']
        land_id = transfer['land_id']
        
        print(f"📋 Found pending transfer: ID {transfer_id} for land {land_id}")
        
        # Try to execute the transfer
        print("⚡ Attempting to execute transfer...")
        response = requests.post(
            f"{BASE_URL}/lands/{land_id}/transfer/{transfer_id}/execute",
            headers=headers
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 400:
            data = response.json()
            if 'solution' in data:
                print(f"\n💡 Solution: {data['solution']}")
                print(f"🔧 Backend address: {data.get('details', {}).get('backend_address', 'N/A')}")
    else:
        print(f"❌ Failed to get transfers: {response.text}")

if __name__ == "__main__":
    test_transfer_execution()