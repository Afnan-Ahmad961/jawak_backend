import requests

BASE_URL = "http://localhost:8000"
VENDOR_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg3MDY3MzkwLCJpYXQiOjE3ODcwNjM3OTAsImp0aSI6IjE0NDYxMzJhYTE4ZTRmNjViN2EwOWUyZmFkODJkNzE4IiwidXNlcl9pZCI6IjE3In0.5FVPQhzxGnSyQrK3qGZR9gPlLE5EeRRAdppJzKz9ZZ4"
CLIENT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg3MDY3MzkwLCJpYXQiOjE3ODcwNjM3OTAsImp0aSI6IjViNDcxNzYxOGVmNzQyMzFhNmE2NDM4ZGNmNjQ0NzVhIiwidXNlcl9pZCI6IjE2In0.aGPMbcKE9xiFlzgUE1E7-olCQIl-ZCk70LCC-9I2L9E"

HEADERS_VENDOR = {
    "Authorization": f"Bearer {VENDOR_TOKEN}",
    "Content-Type": "application/json"
}

HEADERS_CLIENT = {
    "Authorization": f"Bearer {CLIENT_TOKEN}",
    "Content-Type": "application/json"
}


def test_invalid_bid_values_rejected():
    timeout = 30

    # Step 1: Create a design request as client to have a valid design_request id
    design_request_payload = {
        "title": "Test Design Request for Invalid Bid Values",
        "description": "Test description",
        "apparel_type": "hoodie",
        "quantity": 10,
        "material": "cotton",
        "sizes": [{"size": "M", "quantity": 10}],
        "color_preferences": "blue",
        "deadline": "2099-12-31"
    }
    design_request = None
    try:
        resp = requests.post(f"{BASE_URL}/api/v1/requests/",
                             json=design_request_payload,
                             headers=HEADERS_CLIENT,
                             timeout=timeout)
        assert resp.status_code == 201, f"Failed to create design request: {resp.text}"
        design_request = resp.json()
        design_request_id = design_request.get("id")
        assert design_request_id is not None

        url_bids = f"{BASE_URL}/api/v1/bids/"

        # Test proposed_price <= 0 returns 400
        invalid_prices = [0, -10, -0.01]
        for price in invalid_prices:
            bid_payload = {
                "design_request": design_request_id,
                "proposed_price": price,
                "delivery_days": 5,
                "message": "Test bid with invalid price"
            }
            r = requests.post(url_bids, json=bid_payload, headers=HEADERS_VENDOR, timeout=timeout)
            assert r.status_code == 400, f"Expected 400 for proposed_price={price}, got {r.status_code}"

        # Test delivery_days < 1 returns 400
        invalid_delivery_days = [0, -1, -5]
        for days in invalid_delivery_days:
            bid_payload = {
                "design_request": design_request_id,
                "proposed_price": 1000,
                "delivery_days": days,
                "message": "Test bid with invalid delivery days"
            }
            r = requests.post(url_bids, json=bid_payload, headers=HEADERS_VENDOR, timeout=timeout)
            assert r.status_code == 400, f"Expected 400 for delivery_days={days}, got {r.status_code}"

        # Test missing design_request id returns 400 or 404
        bid_payload_missing_id = {
            # purposely omitting "design_request"
            "proposed_price": 1000,
            "delivery_days": 5,
            "message": "Test bid with missing design_request"
        }
        r = requests.post(url_bids, json=bid_payload_missing_id, headers=HEADERS_VENDOR, timeout=timeout)
        assert r.status_code in (400, 404), f"Expected 400 or 404 for missing design_request, got {r.status_code}"

        # Test invalid design_request id returns 400 or 404
        invalid_ids = [-1, 0, 999999999]
        for invalid_id in invalid_ids:
            bid_payload_invalid_id = {
                "design_request": invalid_id,
                "proposed_price": 1000,
                "delivery_days": 5,
                "message": "Test bid with invalid design_request id"
            }
            r = requests.post(url_bids, json=bid_payload_invalid_id, headers=HEADERS_VENDOR, timeout=timeout)
            assert r.status_code in (400, 404), f"Expected 400 or 404 for design_request id {invalid_id}, got {r.status_code}"

    finally:
        # Cleanup: Delete the created design request if exists
        if design_request is not None:
            try:
                del_resp = requests.delete(f"{BASE_URL}/api/v1/requests/{design_request_id}/",
                                          headers=HEADERS_CLIENT,
                                          timeout=timeout)
                # Accept 204 No Content or 404 Not Found (already deleted)
                assert del_resp.status_code in (204, 404)
            except Exception:
                pass


test_invalid_bid_values_rejected()
