#!/usr/bin/env python3
"""
Test registering a new land with backend ownership model
"""

import requests
import json
import time

BASE_URL = "http://localhost:5001/api"

def test_new_land_registration():
    # Login as the user who will own the land
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "demo_user",
        "password": "user123"
    })
    
    if response.status_code == 200:
        user_token = response.json()['access_token']
        print("✅ User login successful")
    else:
        print(f"❌ User login failed: {response.text}")
        return
    
    # Login as admin for approval
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "demo_admin",
        "password": "admin123"
    })
    
    if response.status_code == 200:
        admin_token = response.json()['access_token']
        print("✅ Admin login successful")
    else:
        print(f"❌ Admin login failed: {response.text}")
        return
    
    user_headers = {"Authorization": f"Bearer {user_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Create a new land as the user
    print("🏢 Creating new land with backend ownership model...")
    land_data = {
        "title": "Test Backend Ownership Land",
        "description": "Testing the new backend ownership model",
        "location": "Test Location, Test City",
        "area": 1500,
        "property_type": "residential",
        "property_id": f"TEST{int(time.time())}",  # Unique ID
        "latitude": 40.7128,
        "longitude": -74.0060
    }
    
    response = requests.post(f"{BASE_URL}/lands", headers=user_headers, json=land_data)
    
    if response.status_code == 201:
        land = response.json()['land']
        print(f"✅ Land created: ID {land['id']}")
        print(f"   Title: {land['title']}")
        print(f"   Property ID: {land['property_id']}")
        print(f"   Owner: User (ID: {land['owner_id']})")
        
        # Approve the land as admin
        print("✅ Approving land...")
        approval_data = {"action": "approve", "auto_register": True}
        response = requests.post(
            f"{BASE_URL}/admin/lands/{land['id']}/review",
            headers=admin_headers,
            json=approval_data
        )
        
        if response.status_code == 200:
            print("✅ Land approved and registered on blockchain")
            return land['id']
        else:
            print(f"❌ Land approval failed: {response.text}")
            return None
    else:
        print(f"❌ Land creation failed: {response.text}")
        return None

def test_backend_owned_transfer(land_id):
    """Test transfer with backend-owned land"""
    # Login as user
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "demo_user",
        "password": "user123"
    })
    
    if response.status_code == 200:
        token = response.json()['access_token']
        print("✅ User login successful")
    else:
        print(f"❌ User login failed: {response.text}")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create transfer
    print("🚀 Creating transfer for backend-owned land...")
    transfer_data = {
        "to_user": "test_receiver",
        "price": 300000,
        "transfer_type": "sale"
    }
    
    response = requests.post(
        f"{BASE_URL}/lands/{land_id}/transfer/initiate",
        headers=headers,
        json=transfer_data
    )
    
    if response.status_code == 201:
        transfer = response.json()['transfer']
        print(f"✅ Transfer created: ID {transfer['id']}")
        
        # Execute transfer
        print("⚡ Executing transfer...")
        response = requests.post(
            f"{BASE_URL}/lands/{land_id}/transfer/{transfer['id']}/execute",
            headers=headers
        )
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("🎉 TRANSFER SUCCESSFUL!")
            print(f"   Transaction hash: {result.get('transaction_hash')}")
        else:
            print(f"❌ Transfer failed: {response.text}")
    else:
        print(f"❌ Transfer creation failed: {response.text}")

if __name__ == "__main__":
    land_id = test_new_land_registration()
    if land_id:
        print(f"\n{'='*60}")
        test_backend_owned_transfer(land_id)