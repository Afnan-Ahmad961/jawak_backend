import requests
import datetime

BASE_URL = "http://localhost:8000"
CLIENT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg3MDY3MzkwLCJpYXQiOjE3ODcwNjM3OTAsImp0aSI6IjViNDcxNzYxOGVmNzQyMzFhNmE2NDM4ZGNmNjQ0NzVhIiwidXNlcl9pZCI6IjE2In0.aGPMbcKE9xiFlzgUE1E7-olCQIl-ZCk70LCC-9I2L9E"
VENDOR_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg3MDY3MzkwLCJpYXQiOjE3ODcwNjM3OTAsImp0aSI6IjE0NDYxMzJhYTE4ZTRmNjViN2EwOWUyZmFkODJkNzE4IiwidXNlcl9pZCI6IjE3In0.5FVPQhzxGnSyQrK3qGZR9gPlLE5EeRRAdppJzKz9ZZ4"

HEADERS_CLIENT = {"Authorization": f"Bearer {CLIENT_TOKEN}"}
HEADERS_VENDOR = {"Authorization": f"Bearer {VENDOR_TOKEN}"}

def test_vendor_withdraws_pending_bid():
    # Step 1: Create a Design Request as Client
    request_payload = {
        "title": "Test Hoodie Request for Withdrawal",
        "description": "A hoodie design to test bid withdrawal.",
        "apparel_type": "hoodie",
        "quantity": 10,
        "material": "cotton",
        "sizes": [{"size":"M","quantity":5},{"size":"L","quantity":5}],
        "color_preferences": "blue and white",
        "deadline": (datetime.datetime.utcnow() + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
    }
    request_resp = requests.post(
        f"{BASE_URL}/api/v1/requests/",
        json=request_payload,
        headers=HEADERS_CLIENT,
        timeout=30
    )
    assert request_resp.status_code == 201, f"Failed to create design request: {request_resp.text}"
    design_request = request_resp.json()
    request_id = design_request.get("id")
    assert request_id is not None, "Design request id missing"

    # Use try-finally to ensure cleanup of request
    try:
        # Step 2: Create a Bid as Vendor on the above request
        bid_payload = {
            "design_request": request_id,
            "proposed_price": 1500.00,
            "delivery_days": 20,
            "message": "Bid for test withdrawal"
        }
        bid_resp = requests.post(
            f"{BASE_URL}/api/v1/bids/",
            json=bid_payload,
            headers=HEADERS_VENDOR,
            timeout=30
        )
        assert bid_resp.status_code == 201, f"Failed to create bid: {bid_resp.text}"
        bid = bid_resp.json()
        bid_id = bid.get("id")
        assert bid_id is not None, "Bid id missing"
        assert bid.get("status") == "pending", "Bid status not pending initially"

        # Step 3: Client accepts the bid so it becomes accepted
        accept_payload = {"status": "accepted"}
        accept_resp = requests.patch(
            f"{BASE_URL}/api/v1/bids/{bid_id}/status/",
            json=accept_payload,
            headers=HEADERS_CLIENT,
            timeout=30
        )
        assert accept_resp.status_code == 200, f"Failed to accept bid: {accept_resp.text}"
        accepted_bid = accept_resp.json()
        assert accepted_bid.get("status") == "accepted", "Bid status not updated to accepted"

        # Step 4: Attempt to withdraw the accepted bid as Vendor - expect 400
        withdraw_accepted_resp = requests.post(
            f"{BASE_URL}/api/v1/bids/{bid_id}/withdraw/",
            headers=HEADERS_VENDOR,
            timeout=30
        )
        assert withdraw_accepted_resp.status_code == 400, f"Withdrawing accepted bid did not fail as expected: {withdraw_accepted_resp.text}"

        # Step 5: Create another bid to test pending bid withdrawal
        # Modify message to differentiate
        bid_payload_pending = bid_payload.copy()
        bid_payload_pending["message"] = "Second bid for pending withdrawal"

        # To bypass duplicate error, create new design request
        request_payload2 = {
            "title": "Test Hoodie Request for Pending Withdrawal",
            "description": "A hoodie design to test bid withdrawal pending.",
            "apparel_type": "hoodie",
            "quantity": 5,
            "material": "cotton",
            "sizes": [{"size":"S","quantity":3},{"size":"M","quantity":2}],
            "color_preferences": "red and black",
            "deadline": (datetime.datetime.utcnow() + datetime.timedelta(days=30)).strftime("%Y-%m-%d")
        }
        request_resp2 = requests.post(
            f"{BASE_URL}/api/v1/requests/",
            json=request_payload2,
            headers=HEADERS_CLIENT,
            timeout=30
        )
        assert request_resp2.status_code == 201, f"Failed to create second design request: {request_resp2.text}"
        design_request2 = request_resp2.json()
        request2_id = design_request2.get("id")
        assert request2_id is not None, "Second design request id missing"

        bid_payload_pending["design_request"] = request2_id
        bid_resp2 = requests.post(
            f"{BASE_URL}/api/v1/bids/",
            json=bid_payload_pending,
            headers=HEADERS_VENDOR,
            timeout=30
        )
        assert bid_resp2.status_code == 201, f"Failed to create second bid: {bid_resp2.text}"
        bid2 = bid_resp2.json()
        bid2_id = bid2.get("id")
        assert bid2_id is not None, "Second bid id missing"
        assert bid2.get("status") == "pending", "Second bid status not pending"

        # Step 6: Vendor withdraws the second pending bid
        withdraw_resp = requests.post(
            f"{BASE_URL}/api/v1/bids/{bid2_id}/withdraw/",
            headers=HEADERS_VENDOR,
            timeout=30
        )
        assert withdraw_resp.status_code == 200, f"Failed to withdraw second pending bid: {withdraw_resp.text}"
        withdrawn_bid = withdraw_resp.json()
        assert withdrawn_bid.get("status") == "withdrawn", "Second bid status not updated to withdrawn"

    finally:
        # Cleanup bids
        for bid_id_to_delete in [bid_id, locals().get('bid2_id')]:
            if bid_id_to_delete:
                try:
                    requests.delete(
                        f"{BASE_URL}/api/v1/bids/{bid_id_to_delete}/",
                        headers=HEADERS_VENDOR,
                        timeout=30
                    )
                except Exception:
                    pass
        # Cleanup design requests
        for req_id_to_delete in [request_id, locals().get('request2_id')]:
            if req_id_to_delete:
                try:
                    requests.delete(
                        f"{BASE_URL}/api/v1/requests/{req_id_to_delete}/",
                        headers=HEADERS_CLIENT,
                        timeout=30
                    )
                except Exception:
                    pass

test_vendor_withdraws_pending_bid()