import requests

BASE_URL = "http://localhost:8000"
CLIENT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg3MDY3MzkwLCJpYXQiOjE3ODcwNjM3OTAsImp0aSI6IjViNDcxNzYxOGVmNzQyMzFhNmE2NDM4ZGNmNjQ0NzVhIiwidXNlcl9pZCI6IjE2In0.aGPMbcKE9xiFlzgUE1E7-olCQIl-ZCk70LCC-9I2L9E"
ADMIN_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg3MDY3MzkxLCJpYXQiOjE3ODcwNjM3OTEsImp0aSI6IjI3ZjEwYTg2OWZjOTRiMDk5MmRjY2QwNGQyMmU3Yjg1IiwidXNlcl9pZCI6IjE4In0.S4YpuifNmRKmnB8iD9Y-RmImiX3i1JqOmAvQttW_pvc"

def test_analytics_overview_admin_only():
    url = f"{BASE_URL}/api/v1/analytics/overview/"

    headers_client = {
        "Authorization": f"Bearer {CLIENT_TOKEN}",
        "Accept": "application/json"
    }
    headers_admin = {
        "Authorization": f"Bearer {ADMIN_TOKEN}",
        "Accept": "application/json"
    }

    # Client token access - expect 403
    try:
        resp_client = requests.get(url, headers=headers_client, timeout=30)
    except requests.RequestException as e:
        assert False, f"Client request failed: {e}"
    assert resp_client.status_code == 403, f"Expected 403 for client but got {resp_client.status_code}"

    # Admin token access - expect 200 with JSON response containing aggregate metrics
    try:
        resp_admin = requests.get(url, headers=headers_admin, timeout=30)
    except requests.RequestException as e:
        assert False, f"Admin request failed: {e}"
    assert resp_admin.status_code == 200, f"Expected 200 for admin but got {resp_admin.status_code}"
    try:
        data = resp_admin.json()
    except ValueError:
        assert False, "Admin response is not valid JSON"

    # Validate that the response contains some keys indicating aggregate metrics
    # Since exact keys not specified, check it's a dict with at least one key
    assert isinstance(data, dict), "Admin response data is not a JSON object"
    assert len(data) > 0, "Admin response JSON contains no metrics"

test_analytics_overview_admin_only()