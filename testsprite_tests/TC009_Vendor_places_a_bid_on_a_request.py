import requests
import json

BASE_URL = "http://localhost:8000"
CLIENT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg3MDY3MzkwLCJpYXQiOjE3ODcwNjM3OTAsImp0aSI6IjViNDcxNzYxOGVmNzQyMzFhNmE2NDM4ZGNmNjQ0NzVhIiwidXNlcl9pZCI6IjE2In0.aGPMbcKE9xiFlzgUE1E7-olCQIl-ZCk70LCC-9I2L9E"
VENDOR_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg3MDY3MzkwLCJpYXQiOjE3ODcwNjM3OTAsImp0aSI6IjE0NDYxMzJhYTE4ZTRmNjViN2EwOWUyZmFkODJkNzE4IiwidXNlcl9pZCI6IjE3In0.5FVPQhzxGnSyQrK3qGZR9gPlLE5EeRRAdppJzKz9ZZ4"
TIMEOUT = 30

def test_tc009_vendor_places_a_bid_on_a_request():
    headers_client = {
        "Authorization": f"Bearer {CLIENT_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    headers_vendor = {
        "Authorization": f"Bearer {VENDOR_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    design_request_id = None
    bid_id = None

    # Step 1: Ensure VENDOR has a profile (TC003 prerequisite)
    # We'll try to update/create the vendor profile to be sure it exists
    vendor_profile_payload = {
        "company_name": "Test Vendor Co",
        "location": "Karachi",
        "specialties": ["custom clothing", "streetwear"],
        "capacity": 100
    }
    try:
        resp = requests.put(f"{BASE_URL}/api/v1/vendors/me/", headers=headers_vendor, json=vendor_profile_payload, timeout=TIMEOUT)
        assert resp.status_code == 200, f"Failed to create/update vendor profile, status: {resp.status_code}, body: {resp.text}"
    except Exception as e:
        raise AssertionError(f"Error creating/updating vendor profile: {e}")

    # Step 2: Create a client design request (prereq)
    design_request_payload = {
        "title": "TC009 Test Hoodie Design",
        "description": "A hoodie design for testing vendor bids.",
        "apparel_type": "hoodie",
        "quantity": 10,
        "material": "Cotton",
        "sizes": [{"size": "M", "quantity": 5}, {"size": "L", "quantity": 5}],
        "color_preferences": "Black and white",
        "deadline": "2099-12-31"
    }
    try:
        resp = requests.post(f"{BASE_URL}/api/v1/requests/", headers=headers_client, json=design_request_payload, timeout=TIMEOUT)
        assert resp.status_code == 201, f"Failed to create design request, status: {resp.status_code}, body: {resp.text}"
        design_request = resp.json()
        design_request_id = design_request.get("id") or design_request.get("pk")
        assert design_request_id is not None, "Design request ID not in response"
    except Exception as e:
        raise AssertionError(f"Error creating design request: {e}")

    # Step 3: Vendor places a bid on the design request
    bid_payload = {
        "design_request": design_request_id,
        "proposed_price": 1500.00,
        "delivery_days": 20,
        "message": "We can deliver high quality within 20 days."
    }
    try:
        resp = requests.post(f"{BASE_URL}/api/v1/bids/", headers=headers_vendor, json=bid_payload, timeout=TIMEOUT)
        assert resp.status_code == 201, f"Failed to place bid, status: {resp.status_code}, body: {resp.text}"
        bid = resp.json()
        bid_id = bid.get("id") or bid.get("pk")
        status = bid.get("status")
        assert status == "pending", f"Expected bid status 'pending', got '{status}'"
        # Optional: validate bid fields
        assert bid.get("design_request") == design_request_id, "Bid design_request ID mismatch"
        assert float(bid.get("proposed_price")) == 1500.00, "Bid proposed_price mismatch"
        assert int(bid.get("delivery_days")) == 20, "Bid delivery_days mismatch"
        assert isinstance(bid.get("message"), str) and bid.get("message"), "Bid message missing or empty"
    except Exception as e:
        raise AssertionError(f"Error placing bid: {e}")

    # Cleanup: delete the bid if possible and design request
    # Deleting bid and design request endpoints are not confirmed from PRD for bids.
    # So we'll at least delete the design request if possible.
    # Assuming DELETE /api/v1/requests/{id}/ will delete the design request (owner only)
    try:
        if design_request_id is not None:
            # Use CLIENT token to delete client-owned design request
            del_resp = requests.delete(f"{BASE_URL}/api/v1/requests/{design_request_id}/", headers=headers_client, timeout=TIMEOUT)
            # A 204 (Deleted) expected; if not 204 or 404, raise error
            assert del_resp.status_code in [204, 404], f"Failed to delete design request, status: {del_resp.status_code}, body: {del_resp.text}"
    except Exception as e:
        # Log but don't fail test on cleanup
        pass


test_tc009_vendor_places_a_bid_on_a_request()