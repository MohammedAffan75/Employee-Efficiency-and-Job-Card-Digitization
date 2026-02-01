#!/usr/bin/env python3
"""
Simple test script to verify backend functionality
"""
import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_health():
    """Test health endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"✅ Health check: {response.status_code} - {response.json()}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_login():
    """Test login endpoint"""
    try:
        login_data = {
            "ec_number": "ADMIN001",
            "password": "admin123"
        }
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Login successful: {data.get('access_token', 'No token')[:20]}...")
            return data.get('access_token')
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_activity_codes(token):
    """Test activity codes endpoint"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/activity-codes/", headers=headers)
        print(f"✅ Activity codes: {response.status_code} - {len(response.json()) if response.status_code == 200 else response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Activity codes error: {e}")
        return False

def test_machines(token):
    """Test machines endpoint"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(f"{BASE_URL}/machines/", headers=headers)
        print(f"✅ Machines: {response.status_code} - {len(response.json()) if response.status_code == 200 else response.text}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Machines error: {e}")
        return False

def main():
    print("🧪 Testing Backend API...")
    
    # Test health
    if not test_health():
        print("❌ Backend is not running. Please start it with: uvicorn app.main:app --reload")
        return
    
    # Test login
    token = test_login()
    if not token:
        print("❌ Login failed. Please check if admin user exists.")
        return
    
    # Test protected endpoints
    test_activity_codes(token)
    test_machines(token)
    
    print("🎉 Backend tests complete!")

if __name__ == "__main__":
    main()