import requests

BASE_URL = "http://localhost:8000"
CLIENT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg3MDY3MzkwLCJpYXQiOjE3ODcwNjM3OTAsImp0aSI6IjViNDcxNzYxOGVmNzQyMzFhNmE2NDM4ZGNmNjQ0NzVhIiwidXNlcl9pZCI6IjE2In0.aGPMbcKE9xiFlzgUE1E7-olCQIl-ZCk70LCC-9I2L9E"
VENDOR_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg3MDY3MzkwLCJpYXQiOjE3ODcwNjM3OTAsImp0aSI6IjE0NDYxMzJhYTE4ZTRmNjViN2EwOWUyZmFkODJkNzE4IiwidXNlcl9pZCI6IjE3In0.5FVPQhzxGnSyQrK3qGZR9gPlLE5EeRRAdppJzKz9ZZ4"

def test_client_confirms_delivery_to_complete_order():
    headers_client = {"Authorization": f"Bearer {CLIENT_TOKEN}"}
    headers_vendor = {"Authorization": f"Bearer {VENDOR_TOKEN}"}

    # Step 1: Create a design request as client
    design_request_payload = {
        "title": "Test hoodie delivery confirmation",
        "description": "Test design request for delivery confirmation",
        "apparel_type": "hoodie",
        "quantity": 100,
        "material": "cotton",
        "color_preferences": "blue and white",
        "sizes": [{"size": "M", "quantity": 50}, {"size": "L", "quantity": 50}],
        "deadline": "2030-12-31"
    }
    try:
        resp = requests.post(
            f"{BASE_URL}/api/v1/requests/",
            json=design_request_payload,
            headers=headers_client,
            timeout=30,
        )
        assert resp.status_code == 201, f"Design request creation failed: {resp.text}"
        design_request = resp.json()
        design_request_id = design_request["id"]

        # Step 2: Vendor creates/upserts profile (to pass TC003 prerequisite)
        vendor_profile_payload = {
            "company_name": "Test Vendor Corp",
            "location": "Karachi",
            "specialties": ["hoodie", "tshirt"],
            "capacity": 200
        }
        resp = requests.put(
            f"{BASE_URL}/api/v1/vendors/me/",
            json=vendor_profile_payload,
            headers=headers_vendor,
            timeout=30,
        )
        assert resp.status_code == 200, f"Vendor profile creation failed: {resp.text}"
        vendor_profile = resp.json()
        vendor_id = vendor_profile["id"]

        # Step 3: Vendor places a bid on the design request
        bid_payload = {
            "design_request": design_request_id,
            "proposed_price": 1500.00,
            "delivery_days": 20,
            "message": "We can fulfill your order with quality"
        }
        resp = requests.post(
            f"{BASE_URL}/api/v1/bids/",
            json=bid_payload,
            headers=headers_vendor,
            timeout=30,
        )
        assert resp.status_code == 201, f"Bid creation failed: {resp.text}"
        bid = resp.json()
        bid_id = bid["id"]

        # Step 4: Client accepts the bid (to create order)
        patch_payload = {"status": "accepted"}
        resp = requests.patch(
            f"{BASE_URL}/api/v1/bids/{bid_id}/status/",
            json=patch_payload,
            headers=headers_client,
            timeout=30,
        )
        assert resp.status_code == 200, f"Accepting bid failed: {resp.text}"
        bid_after_accept = resp.json()
        assert bid_after_accept["status"] == "accepted", f"Bid status not accepted"

        # Get orders list for client and find the order linked to this bid
        resp = requests.get(
            f"{BASE_URL}/api/v1/orders/",
            headers=headers_client,
            timeout=30,
        )
        assert resp.status_code == 200, f"Fetching orders failed: {resp.text}"
        orders = resp.json()
        order = None
        for o in orders:
            if o.get("bid") == bid_id or o.get("bid_id") == bid_id or o.get("id") and "bid" in o and o["bid"] == bid_id:
                order = o
                break
        if not order:
            # fallback to first order with matching design_request_id might be necessary
            for o in orders:
                # Sometimes order may contain design_request field or bid info differently
                if "design_request" in o and o["design_request"] == design_request_id:
                    order = o
                    break
        assert order, f"No order found for accepted bid {bid_id}"
        order_id = order["id"]

        # Step 4.5: Vendor posts production update with delivery stage before client confirms delivery
        production_update_payload = {
            "stage": "delivered",
            "note": "Order marked delivered",
            # No image provided
        }
        resp = requests.post(
            f"{BASE_URL}/api/v1/orders/{order_id}/production-updates/",
            json=production_update_payload,
            headers=headers_vendor,
            timeout=30,
        )
        assert resp.status_code == 201, f"Posting production update failed: {resp.text}"

        # Step 5: Client confirms delivery -> POST /api/v1/orders/{order_id}/confirm-delivery/
        resp = requests.post(
            f"{BASE_URL}/api/v1/orders/{order_id}/confirm-delivery/",
            headers=headers_client,
            timeout=30,
        )
        assert resp.status_code == 200, f"Client confirm delivery failed: {resp.text}"
        order_after_confirm = resp.json()
        assert order_after_confirm.get("status") == "completed", f"Order status is not completed after confirm delivery"

        # Step 6: Vendor tries to confirm delivery -> should be forbidden (403 or 401)
        resp = requests.post(
            f"{BASE_URL}/api/v1/orders/{order_id}/confirm-delivery/",
            headers=headers_vendor,
            timeout=30,
        )
        assert resp.status_code in (401, 403), f"Vendor confirm delivery should be forbidden but got {resp.status_code}"

    finally:
        # Cleanup: Delete the created order by deleting the bid and design request if possible
        # Deleting the design request as client, which also would delete related bids and orders
        try:
            requests.delete(
                f"{BASE_URL}/api/v1/requests/{design_request_id}/",
                headers=headers_client,
                timeout=30,
            )
        except Exception:
            pass
        # There is no explicit delete order or bid endpoint mentioned, so best effort cleanup done.

test_client_confirms_delivery_to_complete_order()