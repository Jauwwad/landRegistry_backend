#!/usr/bin/env python3
"""
Quick test to see the transfer history response format
"""

import requests
import json

BASE_URL = "http://localhost:5001/api"

def check_transfer_format():
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
    
    # Get transfer history
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/lands/7/transfer-history", headers=headers)
    
    print(f"Status code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"Data type: {type(data)}")
            if isinstance(data, list) and len(data) > 0:
                print(f"First item type: {type(data[0])}")
                print(f"First item: {data[0]}")
        except Exception as e:
            print(f"JSON parse error: {e}")

if __name__ == "__main__":
    check_transfer_format()