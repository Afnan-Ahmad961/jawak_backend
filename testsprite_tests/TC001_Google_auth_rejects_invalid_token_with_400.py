import requests

BASE_URL = "http://localhost:8000"
ENDPOINT = "/api/v1/user/auth/google/"
INVALID_TOKEN_PAYLOAD = {"access_token": "invalid_token_example"}
TIMEOUT = 30
HEADERS = {
    "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg3MDY3MzkwLCJpYXQiOjE3ODcwNjM3OTAsImp0aSI6IjViNDcxNzYxOGVmNzQyMzFhNmE2NDM4ZGNmNjQ0NzVhIiwidXNlcl9pZCI6IjE2In0.aGPMbcKE9xiFlzgUE1E7-olCQIl-ZCk70LCC-9I2L9E"
}

def test_google_auth_invalid_token_rejects_400():
    url = f"{BASE_URL}{ENDPOINT}"
    try:
        response = requests.post(url, json=INVALID_TOKEN_PAYLOAD, headers=HEADERS, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request failed: {e}"

    assert response.status_code == 400, f"Expected status code 400, got {response.status_code}"

    try:
        error_response = response.json()
    except ValueError:
        assert False, f"Response is not valid JSON: {response.text}"

    expected_error_message = "Invalid or expired Google token."
    # The actual error key is 'access_token' with an error message.
    assert 'access_token' in error_response, f"Expected 'access_token' key in error response, got {error_response}"
    actual_message = error_response['access_token']
    assert actual_message == expected_error_message, f"Expected error message '{expected_error_message}', got '{actual_message}'"


test_google_auth_invalid_token_rejects_400()
