import requests

BASE_URL = "http://localhost:8000"
CLIENT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg3MDY3MzkwLCJpYXQiOjE3ODcwNjM3OTAsImp0aSI6IjViNDcxNzYxOGVmNzQyMzFhNmE2NDM4ZGNmNjQ0NzVhIiwidXNlcl9pZCI6IjE2In0.aGPMbcKE9xiFlzgUE1E7-olCQIl-ZCk70LCC-9I2L9E"
HEADERS = {
    "Authorization": f"Bearer {CLIENT_TOKEN}",
    "Accept": "application/json",
}

def test_list_vendors_and_retrieve_vendor_detail():
    # GET /api/v1/vendors/ with CLIENT token
    url_list = f"{BASE_URL}/api/v1/vendors/"
    try:
        resp_list = requests.get(url_list, headers=HEADERS, timeout=30)
    except requests.RequestException as e:
        assert False, f"Request to list vendors failed: {e}"
    assert resp_list.status_code == 200, f"Expected 200 but got {resp_list.status_code}"
    try:
        vendor_list = resp_list.json()
    except ValueError:
        assert False, "Response from list vendors is not valid JSON"
    assert isinstance(vendor_list, list), "Vendor list should be a JSON array"

    if vendor_list:
        vendor_id = vendor_list[0].get("id")
        assert vendor_id is not None, "Vendor object missing 'id' field"

        # GET /api/v1/vendors/{vendor_id}/ with CLIENT token
        url_detail = f"{BASE_URL}/api/v1/vendors/{vendor_id}/"
        try:
            resp_detail = requests.get(url_detail, headers=HEADERS, timeout=30)
        except requests.RequestException as e:
            assert False, f"Request to get vendor detail failed: {e}"
        assert resp_detail.status_code == 200, f"Expected 200 but got {resp_detail.status_code}"
        try:
            vendor_detail = resp_detail.json()
        except ValueError:
            assert False, "Response from vendor detail is not valid JSON"
        assert vendor_detail.get("id") == vendor_id, "Vendor detail ID does not match requested ID"
    else:
        # If no vendors, we cannot test detail; skip detail test
        vendor_id = None

    # Test 404 for a non-existent vendor ID
    nonexistent_id = 9999999999999
    if vendor_id == nonexistent_id:
        nonexistent_id += 1
    url_404 = f"{BASE_URL}/api/v1/vendors/{nonexistent_id}/"
    try:
        resp_404 = requests.get(url_404, headers=HEADERS, timeout=30)
    except requests.RequestException as e:
        assert False, f"Request to non-existent vendor ID failed: {e}"
    assert resp_404.status_code == 404, f"Expected 404 for non-existent vendor id but got {resp_404.status_code}"

test_list_vendors_and_retrieve_vendor_detail()