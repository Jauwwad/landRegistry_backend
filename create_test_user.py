#!/usr/bin/env python3
"""
Create a second test user for transfer testing
"""

import requests
import json

BASE_URL = "http://localhost:5001/api"

def create_test_user():
    print("👤 Creating second test user...")
    
    user_data = {
        "username": "test_receiver",
        "email": "test_receiver@example.com",
        "password": "password123",
        "first_name": "Test",
        "last_name": "Receiver",
        "phone": "1234567890",
        "wallet_address": "0x742d35Cc6573C0532C8aBb5f69c21Ae1D3e7b93F"  # Different wallet
    }
    
    response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
    
    if response.status_code == 201:
        print("✅ Test receiver user created successfully")
        return True
    elif "already exists" in response.text.lower():
        print("✅ Test receiver user already exists")
        return True
    else:
        print(f"❌ Failed to create user: {response.text}")
        return False

def test_login():
    print("🔐 Testing login for new user...")
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "test_receiver",
        "password": "password123"
    })
    
    if response.status_code == 200:
        print("✅ New user login successful")
        return True
    else:
        print(f"❌ New user login failed: {response.text}")
        return False

if __name__ == "__main__":
    if create_test_user() and test_login():
        print("🎉 Second test user is ready for transfer testing!")
    else:
        print("❌ Failed to set up second test user")