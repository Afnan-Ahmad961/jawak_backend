import requests

BASE_URL = "http://localhost:8000"
CLIENT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg3MDY3MzkwLCJpYXQiOjE3ODcwNjM3OTAsImp0aSI6IjViNDcxNzYxOGVmNzQyMzFhNmE2NDM4ZGNmNjQ0NzVhIiwidXNlcl9pZCI6IjE2In0.aGPMbcKE9xiFlzgUE1E7-olCQIl-ZCk70LCC-9I2L9E"
HEADERS = {
    "Authorization": f"Bearer {CLIENT_TOKEN}",
    "Content-Type": "application/json"
}
TIMEOUT = 30


def test_tc006_client_creates_design_request():
    # Valid request payload
    valid_payload = {
        "title": "Test Design Request",
        "description": "A sample design request for testing.",
        "apparel_type": "hoodie",
        "quantity": 100,
        "material": "cotton",
        "color_preferences": "red, black",
        "sizes": [{"size": "M", "quantity": 50}, {"size": "L", "quantity": 50}]
    }

    # Missing apparel_type and quantity for invalid payload test
    invalid_payloads = [
        {
            "title": "Missing apparel_type",
            "description": "Invalid without apparel_type",
            "quantity": 100,
            "material": "cotton",
            "color_preferences": "red, black",
            "sizes": [{"size": "M", "quantity": 50}, {"size": "L", "quantity": 50}]
        },
        {
            "title": "Missing quantity",
            "description": "Invalid without quantity",
            "apparel_type": "hoodie",
            "material": "cotton",
            "color_preferences": "red, black",
            "sizes": [{"size": "M", "quantity": 50}, {"size": "L", "quantity": 50}]
        }
    ]

    request_id = None
    try:
        # POST valid design request - expect 201 Created
        resp = requests.post(
            f"{BASE_URL}/api/v1/requests/",
            headers=HEADERS,
            json=valid_payload,
            timeout=TIMEOUT
        )
        assert resp.status_code == 201, f"Expected 201, got {resp.status_code}"
        resp_json = resp.json()
        assert "id" in resp_json, "Response missing 'id'"
        assert resp_json.get("status") == "open", f"Expected status 'open', got: {resp_json.get('status')}"
        request_id = resp_json["id"]

        # POST invalid payloads - expect 400 Bad Request
        for payload in invalid_payloads:
            resp_invalid = requests.post(
                f"{BASE_URL}/api/v1/requests/",
                headers=HEADERS,
                json=payload,
                timeout=TIMEOUT
            )
            assert resp_invalid.status_code == 400, (
                f"Expected 400 for invalid payload, got {resp_invalid.status_code} with payload {payload}"
            )
    finally:
        # Clean up: delete created design request if created
        if request_id:
            try:
                del_resp = requests.delete(
                    f"{BASE_URL}/api/v1/requests/{request_id}/",
                    headers=HEADERS,
                    timeout=TIMEOUT
                )
                # Allow either 204 No Content or 200 OK (in case)
                assert del_resp.status_code in [200, 204], f"Cleanup delete failed with status {del_resp.status_code}"
            except Exception:
                pass


test_tc006_client_creates_design_request()