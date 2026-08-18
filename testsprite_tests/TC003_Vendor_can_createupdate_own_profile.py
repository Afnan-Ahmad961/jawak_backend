import requests

BASE_URL = "http://localhost:8000"
VENDOR_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg3MDY3MzkwLCJpYXQiOjE3ODcwNjM3OTAsImp0aSI6IjE0NDYxMzJhYTE4ZTRmNjViN2EwOWUyZmFkODJkNzE4IiwidXNlcl9pZCI6IjE3In0.5FVPQhzxGnSyQrK3qGZR9gPlLE5EeRRAdppJzKz9ZZ4"
TIMEOUT = 30

def test_vendor_can_create_update_own_profile():
    headers = {
        "Authorization": f"Bearer {VENDOR_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    update_data = {
        "company_name": "Test Company Inc.",
        "location": "Karachi, Pakistan",
        "specialties": ["men's wear", "women's wear", "kids"],
        "capacity": 500
    }

    # PUT to create/update vendor profile
    put_url = f"{BASE_URL}/api/v1/vendors/me/"
    try:
        put_response = requests.put(put_url, json=update_data, headers=headers, timeout=TIMEOUT)
        put_response.raise_for_status()
    except requests.RequestException as e:
        assert False, f"PUT /api/v1/vendors/me/ request failed: {e}"

    assert put_response.status_code == 200, f"Expected status 200, got {put_response.status_code}"
    put_json = put_response.json()
    # Validate that returned profile matches updated data
    assert put_json.get("company_name") == update_data["company_name"], "company_name mismatch in PUT response"
    assert put_json.get("location") == update_data["location"], "location mismatch in PUT response"
    assert put_json.get("specialties") == update_data["specialties"], "specialties mismatch in PUT response"
    assert put_json.get("capacity") == update_data["capacity"], "capacity mismatch in PUT response"

    # GET to retrieve own vendor profile and verify updates reflected
    get_url = f"{BASE_URL}/api/v1/vendors/me/"
    try:
        get_response = requests.get(get_url, headers=headers, timeout=TIMEOUT)
        get_response.raise_for_status()
    except requests.RequestException as e:
        assert False, f"GET /api/v1/vendors/me/ request failed: {e}"

    assert get_response.status_code == 200, f"Expected status 200, got {get_response.status_code}"
    get_json = get_response.json()
    assert get_json.get("company_name") == update_data["company_name"], "company_name mismatch in GET response"
    assert get_json.get("location") == update_data["location"], "location mismatch in GET response"
    assert get_json.get("specialties") == update_data["specialties"], "specialties mismatch in GET response"
    assert get_json.get("capacity") == update_data["capacity"], "capacity mismatch in GET response"

test_vendor_can_create_update_own_profile()