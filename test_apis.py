#!/usr/bin/env python3
"""API Testing Script"""

import requests
import json

BASE_URL = "http://127.0.0.1:5001"

def print_response(response, endpoint_name):
    """Print formatted response"""
    print(f"\n{'='*50}")
    print(f"Testing: {endpoint_name}")
    print(f"Status Code: {response.status_code}")
    try:
        print(f"Response: {json.dumps(response.json(), indent=2)}")
    except:
        print(f"Response: {response.text}")
    print(f"{'='*50}")

def test_all_apis():
    """Test all backend APIs"""
    
    # Test health check
    response = requests.get(f"{BASE_URL}/")
    print_response(response, "Health Check")
    
    # Test user registration
    print("\n🔵 Testing User Registration")
    user_data = {
        "username": "test_user",
        "email": "test@example.com",
        "password": "test123",
        "first_name": "Test",
        "last_name": "User",
        "wallet_address": "0x123456789abcdef123456789abcdef123456789a",
        "phone": "+1234567892",
        "address": "123 Test Street"
    }
    response = requests.post(f"{BASE_URL}/api/auth/register", json=user_data)
    print_response(response, "User Registration")
    
    # Test login with demo admin
    print("\n🔵 Testing Admin Login")
    login_data = {
        "username": "demo_admin",
        "password": "admin123"
    }
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    print_response(response, "Admin Login")
    
    admin_token = None
    if response.status_code == 200:
        admin_token = response.json().get('token')
    
    # Test login with demo user
    print("\n🔵 Testing User Login")
    login_data = {
        "username": "demo_user",
        "password": "user123"
    }
    response = requests.post(f"{BASE_URL}/api/auth/login", json=login_data)
    print_response(response, "User Login")
    
    user_token = None
    if response.status_code == 200:
        user_token = response.json().get('token')
    
    # Test protected routes if we have tokens
    if user_token:
        headers = {"Authorization": f"Bearer {user_token}"}
        
        # Test profile
        print("\n🔵 Testing User Profile")
        response = requests.get(f"{BASE_URL}/api/auth/profile", headers=headers)
        print_response(response, "User Profile")
        
        # Test lands list
        print("\n🔵 Testing Lands List")
        response = requests.get(f"{BASE_URL}/api/lands", headers=headers)
        print_response(response, "Lands List")
        
        # Test user's lands
        print("\n🔵 Testing User's Lands")
        response = requests.get(f"{BASE_URL}/api/lands/my-lands", headers=headers)
        print_response(response, "User's Lands")
        
        # Test land registration
        print("\n🔵 Testing Land Registration")
        land_data = {
            "property_id": "TEST001",
            "title": "Test Property",
            "description": "A test property for API testing",
            "location": "Test Location",
            "area": 1000.0,
            "property_type": "residential",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "price": 100000.0
        }
        response = requests.post(f"{BASE_URL}/api/lands/register", json=land_data, headers=headers)
        print_response(response, "Land Registration")
        
        land_id = None
        if response.status_code == 201:
            land_id = response.json().get('land', {}).get('id')
        
        # Test land details
        if land_id:
            print("\n🔵 Testing Land Details")
            response = requests.get(f"{BASE_URL}/api/lands/{land_id}", headers=headers)
            print_response(response, "Land Details")
    
    # Test admin routes if we have admin token
    if admin_token:
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Test admin dashboard
        print("\n🔵 Testing Admin Dashboard")
        response = requests.get(f"{BASE_URL}/api/admin/dashboard", headers=admin_headers)
        print_response(response, "Admin Dashboard")
        
        # Test all users
        print("\n🔵 Testing All Users (Admin)")
        response = requests.get(f"{BASE_URL}/api/admin/users", headers=admin_headers)
        print_response(response, "All Users")
        
        # Test all lands
        print("\n🔵 Testing All Lands (Admin)")
        response = requests.get(f"{BASE_URL}/api/admin/lands", headers=admin_headers)
        print_response(response, "All Lands")
        
        # Test land verification (if we have a land to verify)
        response = requests.get(f"{BASE_URL}/api/admin/lands", headers=admin_headers)
        if response.status_code == 200:
            lands = response.json().get('lands', [])
            if lands:
                land_to_verify = lands[0]['id']
                print("\n🔵 Testing Land Verification")
                response = requests.put(f"{BASE_URL}/api/admin/lands/{land_to_verify}/verify", headers=admin_headers)
                print_response(response, "Land Verification")

if __name__ == '__main__':
    print("🚀 Starting Backend API Tests...")
    test_all_apis()
    print("\n✅ API Testing Complete!")