import requests

BASE_URL = "http://localhost:8000"
CLIENT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg3MDY3MzkwLCJpYXQiOjE3ODcwNjM3OTAsImp0aSI6IjViNDcxNzYxOGVmNzQyMzFhNmE2NDM4ZGNmNjQ0NzVhIiwidXNlcl9pZCI6IjE2In0.aGPMbcKE9xiFlzgUE1E7-olCQIl-ZCk70LCC-9I2L9E"
VENDOR_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg3MDY3MzkwLCJpYXQiOjE3ODcwNjM3OTAsImp0aSI6IjE0NDYxMzJhYTE4ZTRmNjViN2EwOWUyZmFkODJkNzE4IiwidXNlcl9pZCI6IjE3In0.5FVPQhzxGnSyQrK3qGZR9gPlLE5EeRRAdppJzKz9ZZ4"

HEADERS_CLIENT = {
    "Authorization": f"Bearer {CLIENT_TOKEN}",
    "Content-Type": "application/json"
}
HEADERS_VENDOR = {
    "Authorization": f"Bearer {VENDOR_TOKEN}",
    "Content-Type": "application/json"
}


def test_only_owner_can_update_design_request():
    # Step 1: Create a design request with CLIENT token
    create_url = f"{BASE_URL}/api/v1/requests/"
    create_payload = {
        "title": "Test Hoodie",
        "description": "Test description for hoodie",
        "apparel_type": "hoodie",
        "quantity": 10,
        "material": "cotton",
        "sizes": [{"size": "M", "quantity": 5}, {"size": "L", "quantity": 5}],
        "color_preferences": "blue and white",
        "deadline": "2026-12-31"
    }

    create_resp = requests.post(create_url, headers=HEADERS_CLIENT, json=create_payload, timeout=30)
    assert create_resp.status_code == 201, f"Failed to create design request: {create_resp.text}"
    design_request = create_resp.json()
    request_id = design_request.get("id")
    assert request_id is not None, "No request_id returned"

    try:
        # Step 2: PATCH with CLIENT token - should succeed with 200
        patch_url = f"{BASE_URL}/api/v1/requests/{request_id}/"
        patch_payload_client = {
            "description": "Updated description by owner"
        }
        patch_resp_client = requests.patch(patch_url, headers=HEADERS_CLIENT, json=patch_payload_client, timeout=30)
        assert patch_resp_client.status_code == 200, f"Owner update failed: {patch_resp_client.text}"
        updated_data = patch_resp_client.json()
        assert updated_data.get("description") == patch_payload_client["description"], "Description not updated by owner"

        # Step 3: PATCH with VENDOR token - should be forbidden (403) or not found (404)
        patch_payload_vendor = {
            "description": "Malicious update by vendor"
        }
        patch_resp_vendor = requests.patch(patch_url, headers=HEADERS_VENDOR, json=patch_payload_vendor, timeout=30)
        assert patch_resp_vendor.status_code in (403, 404), f"Non-owner update must be forbidden or not found, got {patch_resp_vendor.status_code}"
    finally:
        # Clean up: Delete the design request with CLIENT token
        delete_url = f"{BASE_URL}/api/v1/requests/{request_id}/"
        delete_resp = requests.delete(delete_url, headers=HEADERS_CLIENT, timeout=30)
        assert delete_resp.status_code == 204, f"Failed to delete design request: {delete_resp.text}"


test_only_owner_can_update_design_request()