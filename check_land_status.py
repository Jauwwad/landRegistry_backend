#!/usr/bin/env python3
"""
Land status checker - Check current land status and blockchain registration
"""

import requests
import json

BASE_URL = "http://localhost:5001/api"

def check_land_status():
    # Login as admin to see all lands
    print("🔐 Logging in as admin...")
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "demo_admin",
        "password": "admin123"
    })
    
    if response.status_code != 200:
        print(f"❌ Admin login failed: {response.text}")
        return
    
    admin_token = response.json()['access_token']
    print("✅ Admin login successful")
    
    # Get all lands from user endpoint
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = requests.get(f"{BASE_URL}/lands", headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Failed to get lands: {response.text}")
        return
    
    lands_data = response.json()
    lands = lands_data.get('lands', [])
    print(f"\n📊 Total lands found: {len(lands)}")
    print("=" * 80)
    
    for land in lands:
        print(f"ID: {land['id']} | Title: {land['title']}")
        print(f"   Status: {land['status']} | Blockchain: {land.get('is_registered_on_blockchain', False)}")
        print(f"   Token ID: {land.get('token_id', 'None')} | Owner: {land.get('owner', {}).get('username', 'Unknown')}")
        print(f"   Wallet: {land.get('wallet_address', 'None')}")
        print("-" * 80)
    
    # Count by status
    status_counts = {}
    blockchain_count = 0
    for land in lands:
        status = land['status']
        status_counts[status] = status_counts.get(status, 0) + 1
        if land.get('is_registered_on_blockchain'):
            blockchain_count += 1
    
    print("\n📈 Summary:")
    for status, count in status_counts.items():
        print(f"   {status}: {count}")
    print(f"   Blockchain registered: {blockchain_count}")

if __name__ == "__main__":
    check_land_status()