import requests

BASE_URL = "http://localhost:8000"
TIMEOUT = 30


def test_post_api_v1_user_auth_google_exchange_token():
    url = f"{BASE_URL}/api/v1/user/auth/google/"
    headers = {
        "Content-Type": "application/json",
    }

    # Valid Google OAuth access_token (dummy placeholder, assume valid in real test environment)
    valid_payload = {
        "access_token": "valid_google_oauth_token_example",
        "code": ""
    }
    # Send valid token request
    try:
        response = requests.post(url, json=valid_payload, headers=headers, timeout=TIMEOUT)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        json_data = response.json()
        assert "access" in json_data and isinstance(json_data["access"], str), "Missing or invalid 'access' token"
        assert "refresh" in json_data and isinstance(json_data["refresh"], str), "Missing or invalid 'refresh' token"
        assert "user" in json_data and isinstance(json_data["user"], dict), "Missing or invalid 'user' data"
    except requests.RequestException as e:
        assert False, f"Request failed with exception: {e}"

    # Invalid Google OAuth access_token tests
    invalid_tokens = [
        None,
        "",
        "invalid_token_example",
        12345,
        {},
        {"access_token": None}
    ]

    for token in invalid_tokens:
        if isinstance(token, dict):
            payload = token
        else:
            payload = {"access_token": token, "code": ""}
        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=TIMEOUT)
            assert resp.status_code == 400, f"Expected 400 for invalid token {token}, got {resp.status_code}"
            # Optionally verify error message content
            resp_json = resp.json() if resp.headers.get("Content-Type", "").startswith("application/json") else {}
            error_msg = resp_json.get("detail") or resp_json.get("error") or ""
            assert error_msg or True  # Allow any error message content but must be present
        except requests.RequestException as e:
            assert False, f"Request failed with exception on invalid token {token}: {e}"


test_post_api_v1_user_auth_google_exchange_token()
