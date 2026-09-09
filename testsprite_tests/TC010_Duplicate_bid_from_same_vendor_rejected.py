import requests

BASE_URL = "http://localhost:8000"
CLIENT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg3MDY3MzkwLCJpYXQiOjE3ODcwNjM3OTAsImp0aSI6IjViNDcxNzYxOGVmNzQyMzFhNmE2NDM4ZGNmNjQ0NzVhIiwidXNlcl9pZCI6IjE2In0.aGPMbcKE9xiFlzgUE1E7-olCQIl-ZCk70LCC-9I2L9E"
VENDOR_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg3MDY3MzkwLCJpYXQiOjE3ODcwNjM3OTAsImp0aSI6IjE0NDYxMzJhYTE4ZTRmNjViN2EwOWUyZmFkODJkNzE4IiwidXNlcl9pZCI6IjE3In0.5FVPQhzxGnSyQrK3qGZR9gPlLE5EeRRAdppJzKz9ZZ4"

HEADERS_CLIENT = {"Authorization": f"Bearer {CLIENT_TOKEN}"}
HEADERS_VENDOR = {"Authorization": f"Bearer {VENDOR_TOKEN}"}

def test_TC010_duplicate_bid_from_same_vendor_rejected():
    design_request_id = None
    first_bid_id = None
    try:
        # Step 1: Create a design request with CLIENT token
        design_request_payload = {
            "title": "TC010 Test Design Request",
            "description": "Test description for duplicate bid check",
            "apparel_type": "hoodie",
            "quantity": 10,
            "material": "cotton",
            "sizes": [{"size": "M", "quantity": 5}, {"size": "L", "quantity": 5}],
            "color_preferences": "blue",
            "deadline": "2099-12-31"
        }
        r_req = requests.post(
            f"{BASE_URL}/api/v1/requests/",
            json=design_request_payload,
            headers=HEADERS_CLIENT,
            timeout=30,
        )
        assert r_req.status_code == 201, f"Failed to create design request: {r_req.text}"
        design_request = r_req.json()
        design_request_id = design_request.get("id")
        assert design_request_id is not None

        # Step 2: Place first bid with VENDOR token
        bid_payload = {
            "design_request": design_request_id,
            "proposed_price": 1500.00,
            "delivery_days": 20,
            "message": "First bid for TC010"
        }
        r_bid = requests.post(
            f"{BASE_URL}/api/v1/bids/",
            json=bid_payload,
            headers=HEADERS_VENDOR,
            timeout=30,
        )
        assert r_bid.status_code == 201, f"Failed to place first bid: {r_bid.text}"
        bid = r_bid.json()
        first_bid_id = bid.get("id")
        assert first_bid_id is not None
        assert bid.get("status") == "pending"

        # Step 3: Place duplicate bid with the same vendor and same design request - expect 400
        r_dup_bid = requests.post(
            f"{BASE_URL}/api/v1/bids/",
            json=bid_payload,
            headers=HEADERS_VENDOR,
            timeout=30,
        )
        assert r_dup_bid.status_code == 400, f"Expected 400 for duplicate bid but got {r_dup_bid.status_code}: {r_dup_bid.text}"

    finally:
        # Cleanup: delete the first bid if exists
        if first_bid_id is not None:
            # No delete endpoint for bids is defined in PRD; so skip bid cleanup.
            pass

        # Cleanup: delete the design request
        if design_request_id is not None:
            requests.delete(
                f"{BASE_URL}/api/v1/requests/{design_request_id}/",
                headers=HEADERS_CLIENT,
                timeout=30,
            )

test_TC010_duplicate_bid_from_same_vendor_rejected()