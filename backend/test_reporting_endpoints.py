"""Quick test script to verify reporting endpoints are accessible"""
import requests

BASE_URL = "http://localhost:8000/api/reporting"

endpoints = [
    "/activity-distribution?employee_id=1&start=2025-01-01&end=2025-12-31",
    "/monthly-trend?employee_id=1&start=2025-01-01&end=2025-12-31",
    "/team-efficiency?team_id=Alpha&start=2025-11-01&end=2025-11-08",
    "/team-trend?team_id=Alpha",
    "/employee-comparison?team_id=Alpha",
    "/dashboard/summary?team_id=Alpha&start=2025-11-01&end=2025-11-08",
]

print("=" * 80)
print("Testing Reporting Endpoints")
print("=" * 80)

for endpoint in endpoints:
    url = f"{BASE_URL}{endpoint}"
    try:
        response = requests.get(url, timeout=5)
        status = "✅" if response.status_code == 200 else f"❌ ({response.status_code})"
        print(f"{status} {endpoint}")
        if response.status_code != 200:
            print(f"    Error: {response.text[:100]}")
    except Exception as e:
        print(f"❌ {endpoint}")
        print(f"    Error: {str(e)[:100]}")

print("\n" + "=" * 80)
print("Test Complete!")
print("=" * 80)
