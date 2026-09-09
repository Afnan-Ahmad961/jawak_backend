import requests

BASE_URL = "http://localhost:8000"
CLIENT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg3MDY3MzkwLCJpYXQiOjE3ODcwNjM3OTAsImp0aSI6IjViNDcxNzYxOGVmNzQyMzFhNmE2NDM4ZGNmNjQ0NzVhIiwidXNlcl9pZCI6IjE2In0.aGPMbcKE9xiFlzgUE1E7-olCQIl-ZCk70LCC-9I2L9E"
VENDOR_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg3MDY3MzkwLCJpYXQiOjE3ODcwNjM3OTAsImp0aSI6IjE0NDYxMzJhYTE4ZTRmNjViN2EwOWUyZmFkODJkNzE4IiwidXNlcl9pZCI6IjE3In0.5FVPQhzxGnSyQrK3qGZR9gPlLE5EeRRAdppJzKz9ZZ4"

HEADERS_CLIENT = {"Authorization": f"Bearer {CLIENT_TOKEN}"}
HEADERS_VENDOR = {"Authorization": f"Bearer {VENDOR_TOKEN}"}
TIMEOUT = 30


def test_TC012_client_accepts_bid_creates_order():
    # 1. Create a new design request using CLIENT token
    request_payload = {
        "title": "Test design request for TC012",
        "description": "Request description for TC012",
        "apparel_type": "hoodie",
        "quantity": 10,
        "material": "cotton",
        "sizes": [{"size": "M", "quantity": 5}, {"size": "L", "quantity": 5}],
        "color_preferences": "blue, black",
        "deadline": "2026-12-31"
    }
    r_req = requests.post(
        f"{BASE_URL}/api/v1/requests/",
        json=request_payload,
        headers=HEADERS_CLIENT,
        timeout=TIMEOUT,
    )
    assert r_req.status_code == 201, f"Design request creation failed: {r_req.text}"
    design_request = r_req.json()
    design_request_id = design_request.get("id")
    assert design_request_id is not None

    # 2. Vendor must have a profile for bidding. Try to get vendor profile; if 404 create it
    r_get_vendor_profile = requests.get(
        f"{BASE_URL}/api/v1/vendors/me/",
        headers=HEADERS_VENDOR,
        timeout=TIMEOUT,
    )
    if r_get_vendor_profile.status_code == 404:
        # Create vendor profile
        vendor_profile_payload = {
            "company_name": "Vendor TC012",
            "location": "Karachi",
            "specialties": ["hoodies", "jackets"],
            "capacity": 100,
        }
        r_create_vendor_profile = requests.put(
            f"{BASE_URL}/api/v1/vendors/me/",
            json=vendor_profile_payload,
            headers=HEADERS_VENDOR,
            timeout=TIMEOUT,
        )
        assert r_create_vendor_profile.status_code == 200, f"Vendor profile creation failed: {r_create_vendor_profile.text}"

    elif r_get_vendor_profile.status_code != 200:
        raise AssertionError(
            f"Unexpected response getting vendor profile: {r_get_vendor_profile.status_code} {r_get_vendor_profile.text}"
        )

    # 3. Place a bid with VENDOR token on the design request created
    bid_payload = {
        "design_request": design_request_id,
        "proposed_price": 1500.00,
        "delivery_days": 20,
        "message": "Bid for TC012 test case",
    }
    r_bid = requests.post(
        f"{BASE_URL}/api/v1/bids/",
        json=bid_payload,
        headers=HEADERS_VENDOR,
        timeout=TIMEOUT,
    )
    assert r_bid.status_code == 201, f"Bid creation failed: {r_bid.text}"
    bid = r_bid.json()
    bid_id = bid.get("id")
    assert bid_id is not None
    assert bid.get("status") == "pending"

    try:
        # 4. With CLIENT token, accept the bid by PATCHing status to 'accepted'
        bid_status_payload = {"status": "accepted"}
        r_accept = requests.patch(
            f"{BASE_URL}/api/v1/bids/{bid_id}/status/",
            json=bid_status_payload,
            headers=HEADERS_CLIENT,
            timeout=TIMEOUT,
        )
        assert r_accept.status_code == 200, f"Bid accept failed: {r_accept.text}"
        accepted_bid = r_accept.json()
        assert accepted_bid.get("status") == "accepted"

        # 5. Verify parent request status is 'awarded'
        r_get_request = requests.get(
            f"{BASE_URL}/api/v1/requests/{design_request_id}/",
            headers=HEADERS_CLIENT,
            timeout=TIMEOUT,
        )
        assert r_get_request.status_code == 200, f"Get request failed: {r_get_request.text}"
        request_data = r_get_request.json()

        req_status = request_data.get("status")
        assert req_status == "awarded", f"Expected request status 'awarded', got '{req_status}'"

        # 6. Verify GET /api/v1/orders/ with CLIENT token includes the new order created
        r_orders = requests.get(
            f"{BASE_URL}/api/v1/orders/",
            headers=HEADERS_CLIENT,
            timeout=TIMEOUT,
        )
        assert r_orders.status_code == 200, f"Get orders failed: {r_orders.text}"
        orders = r_orders.json()
        assert isinstance(orders, list)

        # Find an order that is associated with the accepted bid
        matching_orders = [
            o for o in orders if (
                ("bid" in o and o["bid"] == bid_id) or
                ("bid_id" in o and o["bid_id"] == bid_id) or
                ("design_request" in o and o["design_request"] == design_request_id)
            )
        ]
        assert matching_orders, "No order found corresponding to accepted bid"

    finally:
        # Cleanup: delete the bid if exists by rejecting if still pending or accepted (if API allows)
        # Then delete design request

        # Attempt to reject bid to remove it if possible
        try:
            r_patch_bid_reject = requests.patch(
                f"{BASE_URL}/api/v1/bids/{bid_id}/status/",
                json={"status": "rejected"},
                headers=HEADERS_CLIENT,
                timeout=TIMEOUT,
            )
            # Ignore if not allowed
        except Exception:
            pass

        # Delete the design request
        try:
            r_del_request = requests.delete(
                f"{BASE_URL}/api/v1/requests/{design_request_id}/",
                headers=HEADERS_CLIENT,
                timeout=TIMEOUT,
            )
            # Ignore if already deleted
        except Exception:
            pass


test_TC012_client_accepts_bid_creates_order()