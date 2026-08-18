import requests

BASE_URL = "http://localhost:8000"
CLIENT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg3MDY3MzkwLCJpYXQiOjE3ODcwNjM3OTAsImp0aSI6IjViNDcxNzYxOGVmNzQyMzFhNmE2NDM4ZGNmNjQ0NzVhIiwidXNlcl9pZCI6IjE2In0.aGPMbcKE9xiFlzgUE1E7-olCQIl-ZCk70LCC-9I2L9E"

def test_get_me_requires_auth_and_returns_current_user():
    url = f"{BASE_URL}/api/v1/user/me/"
    timeout_seconds = 30

    # Without Authorization header: should return 401 Unauthorized
    try:
        response = requests.get(url, timeout=timeout_seconds)
    except requests.RequestException as e:
        assert False, f"Request failed unexpectedly without auth: {e}"
    assert response.status_code == 401, f"Expected 401 without auth, got {response.status_code}"

    # With CLIENT bearer token: should return 200 and correct user info
    headers = {
        "Authorization": f"Bearer {CLIENT_TOKEN}"
    }
    try:
        auth_response = requests.get(url, headers=headers, timeout=timeout_seconds)
    except requests.RequestException as e:
        assert False, f"Request failed unexpectedly with auth: {e}"

    assert auth_response.status_code == 200, f"Expected 200 with valid auth, got {auth_response.status_code}"

    try:
        data = auth_response.json()
    except ValueError:
        assert False, "Response body is not valid JSON"

    assert isinstance(data, dict), "Response JSON is not an object"

    expected_email = "ts_client@example.com"
    expected_role = "client"

    assert data.get("email") == expected_email, f"Expected email '{expected_email}', got '{data.get('email')}'"
    assert data.get("role") == expected_role, f"Expected role '{expected_role}', got '{data.get('role')}'"


test_get_me_requires_auth_and_returns_current_user()