import requests
import datetime

BASE_URL = "http://localhost:8000"
CLIENT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg3MDY3MzkwLCJpYXQiOjE3ODcwNjM3OTAsImp0aSI6IjViNDcxNzYxOGVmNzQyMzFhNmE2NDM4ZGNmNjQ0NzVhIiwidXNlcl9pZCI6IjE2In0.aGPMbcKE9xiFlzgUE1E7-olCQIl-ZCk70LCC-9I2L9E"
VENDOR_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg3MDY3MzkwLCJpYXQiOjE3ODcwNjM3OTAsImp0aSI6IjE0NDYxMzJhYTE4ZTRmNjViN2EwOWUyZmFkODJkNzE4IiwidXNlcl9pZCI6IjE3In0.5FVPQhzxGnSyQrK3qGZR9gPlLE5EeRRAdppJzKz9ZZ4"
ADMIN_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg3MDY3MzkxLCJpYXQiOjE3ODcwNjM3OTEsImp0aSI6IjI3ZjEwYTg2OWZjOTRiMDk5MmRjY2QwNGQyMmU3Yjg1IiwidXNlcl9pZCI6IjE4In0.S4YpuifNmRKmnB8iD9Y-RmImiX3i1JqOmAvQttW_pvc"

HEADERS_CLIENT = {"Authorization": f"Bearer {CLIENT_TOKEN}"}
HEADERS_VENDOR = {"Authorization": f"Bearer {VENDOR_TOKEN}"}
HEADERS_ADMIN = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
TIMEOUT = 30


def test_tc019_disputes_raise_on_order_and_admin_resolves():
    order_id = None
    dispute_id = None

    # Step 1: Create prerequisite data - design request by CLIENT
    design_request_data = {
        "title": "Test Hoodie",
        "description": "Test hoodie order for dispute",
        "apparel_type": "hoodie",
        "quantity": 10,
        "material": "cotton",
        "sizes": ["M", "L"],
        "color_preferences": "blue",
        "deadline": (datetime.date.today() + datetime.timedelta(days=10)).isoformat()
    }
    try:
        # Create design request
        resp = requests.post(
            f"{BASE_URL}/api/v1/requests/",
            json=design_request_data,
            headers=HEADERS_CLIENT,
            timeout=TIMEOUT
        )
        assert resp.status_code == 201, f"Design request creation failed: {resp.text}"
        design_request = resp.json()
        design_request_id = design_request["id"]

        # Step 2: Vendor places a bid on design request
        bid_data = {
            "design_request": design_request_id,
            "proposed_price": 1000,
            "delivery_days": 7,
            "message": "I can do this"
        }
        resp = requests.post(
            f"{BASE_URL}/api/v1/bids/",
            json=bid_data,
            headers=HEADERS_VENDOR,
            timeout=TIMEOUT
        )
        assert resp.status_code == 201, f"Bid creation failed: {resp.text}"
        bid = resp.json()
        bid_id = bid["id"]

        # Step 3: Client accepts the bid (which creates an order)
        patch_status_data = {"status": "accepted"}
        resp = requests.patch(
            f"{BASE_URL}/api/v1/bids/{bid_id}/status/",
            json=patch_status_data,
            headers=HEADERS_CLIENT,
            timeout=TIMEOUT
        )
        assert resp.status_code == 200, f"Accepting bid failed: {resp.text}"

        # Get orders and find the created order related to bid
        resp = requests.get(
            f"{BASE_URL}/api/v1/orders/",
            headers=HEADERS_CLIENT,
            timeout=TIMEOUT
        )
        assert resp.status_code == 200, f"Fetching orders failed: {resp.text}"
        orders = resp.json()
        order_id = None
        for order in orders:
            if order.get("bid") == bid_id:
                order_id = order["id"]
                break
        assert order_id is not None, "Order not found after bid acceptance"

        # Step 4: CLIENT raises a dispute on the order
        dispute_data = {
            "order": order_id,
            "reason": "Item not as described",
            "description": "The delivered hoodie color is different than requested"
        }
        resp = requests.post(
            f"{BASE_URL}/api/v1/disputes/",
            json=dispute_data,
            headers=HEADERS_CLIENT,
            timeout=TIMEOUT
        )
        assert resp.status_code == 201, f"Dispute creation failed: {resp.text}"
        dispute = resp.json()
        dispute_id = dispute["id"]
        assert dispute.get("status") == "open", f"New dispute status is not 'open': {dispute.get('status')}"

        # Step 5: CLIENT tries to PATCH the dispute - must be forbidden 403
        patch_data_client = {"status": "resolved", "resolution": "Refund issued"}
        resp = requests.patch(
            f"{BASE_URL}/api/v1/disputes/{dispute_id}/",
            json=patch_data_client,
            headers=HEADERS_CLIENT,
            timeout=TIMEOUT
        )
        assert resp.status_code == 403, f"Non-admin dispute patch did not return 403: {resp.status_code} {resp.text}"

        # Step 6: ADMIN patches dispute to resolved with resolution
        patch_data_admin = {"status": "resolved", "resolution": "Refund issued"}
        resp = requests.patch(
            f"{BASE_URL}/api/v1/disputes/{dispute_id}/",
            json=patch_data_admin,
            headers=HEADERS_ADMIN,
            timeout=TIMEOUT
        )
        assert resp.status_code == 200, f"Admin dispute patch failed: {resp.text}"
        updated_dispute = resp.json()
        assert updated_dispute.get("status") == "resolved", f"Dispute status is not 'resolved': {updated_dispute.get('status')}"
        assert updated_dispute.get("resolution") == "Refund issued", f"Dispute resolution mismatch: {updated_dispute.get('resolution')}"

    finally:
        # Cleanup: Delete dispute if created
        if dispute_id is not None:
            try:
                requests.delete(
                    f"{BASE_URL}/api/v1/disputes/{dispute_id}/",
                    headers=HEADERS_ADMIN,
                    timeout=TIMEOUT
                )
            except Exception:
                pass
        # Cleanup: Delete order if created
        if order_id is not None:
            try:
                requests.delete(
                    f"{BASE_URL}/api/v1/orders/{order_id}/",
                    headers=HEADERS_CLIENT,
                    timeout=TIMEOUT
                )
            except Exception:
                pass
        # Cleanup: Delete bid if created
        if 'bid_id' in locals():
            try:
                requests.delete(
                    f"{BASE_URL}/api/v1/bids/{bid_id}/",
                    headers=HEADERS_VENDOR,
                    timeout=TIMEOUT
                )
            except Exception:
                pass
        # Cleanup: Delete design request if created
        if 'design_request_id' in locals():
            try:
                requests.delete(
                    f"{BASE_URL}/api/v1/requests/{design_request_id}/",
                    headers=HEADERS_CLIENT,
                    timeout=TIMEOUT
                )
            except Exception:
                pass


test_tc019_disputes_raise_on_order_and_admin_resolves()