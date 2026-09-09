import requests
import io

BASE_URL = "http://localhost:8000"
CLIENT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg3MDY3MzkwLCJpYXQiOjE3ODcwNjM3OTAsImp0aSI6IjViNDcxNzYxOGVmNzQyMzFhNmE2NDM4ZGNmNjQ0NzVhIiwidXNlcl9pZCI6IjE2In0.aGPMbcKE9xiFlzgUE1E7-olCQIl-ZCk70LCC-9I2L9E"
VENDOR_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg3MDY3MzkwLCJpYXQiOjE3ODcwNjM3OTAsImp0aSI6IjE0NDYxMzJhYTE4ZTRmNjViN2EwOWUyZmFkODJkNzE4IiwidXNlcl9pZCI6IjE3In0.5FVPQhzxGnSyQrK3qGZR9gPlLE5EeRRAdppJzKz9ZZ4"
HEADERS_CLIENT = {"Authorization": f"Bearer {CLIENT_TOKEN}"}
HEADERS_VENDOR = {"Authorization": f"Bearer {VENDOR_TOKEN}"}
TIMEOUT = 30

# This is a minimal valid 1x1 PNG image byte stream to replace PIL image creation
MINIMAL_PNG_BYTES = (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
                     b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00"
                     b"\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc`\x00\x00\x00\x02\x00\x01"
                     b"\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82")

def create_design_request():
    url = f"{BASE_URL}/api/v1/requests/"
    json_data = {
        "title": "Test Hoodie Design",
        "description": "Test description for hoodie design.",
        "apparel_type": "hoodie",
        "quantity": 10,
        "material": "cotton",
        "sizes": ["M", "L"],
        "color_preferences": "blue and white",
        "deadline": "2030-12-31"
    }
    resp = requests.post(url, headers=HEADERS_CLIENT, json=json_data, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()

def upload_reference_image(request_id):
    url = f"{BASE_URL}/api/v1/requests/{request_id}/reference-images/"
    buf = io.BytesIO(MINIMAL_PNG_BYTES)
    buf.seek(0)
    # Move label into files as (None, label) to encode as multipart form field
    files = {
        'image': ('image.png', buf, 'image/png'),
        'label': (None, 'Red square')
    }
    resp = requests.post(url, headers=HEADERS_CLIENT, files=files, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()

def create_vendor_profile():
    url = f"{BASE_URL}/api/v1/vendors/me/"
    json_data = {
        "company_name": "Test Vendor Ltd",
        "location": "Karachi",
        "specialties": ["hoodie", "jacket"],
        "capacity": 50
    }
    resp = requests.put(url, headers=HEADERS_VENDOR, json=json_data, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()

def place_bid(design_request_id):
    url = f"{BASE_URL}/api/v1/bids/"
    json_data = {
        "design_request": design_request_id,
        "proposed_price": 1500,
        "delivery_days": 15,
        "message": "Competitive bid with quality materials"
    }
    resp = requests.post(url, headers=HEADERS_VENDOR, json=json_data, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()

def accept_bid(bid_id):
    url = f"{BASE_URL}/api/v1/bids/{bid_id}/status/"
    json_data = {"status": "accepted"}
    resp = requests.patch(url, headers=HEADERS_CLIENT, json=json_data, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()

def get_order_by_bid(bid_id):
    url = f"{BASE_URL}/api/v1/orders/"
    resp = requests.get(url, headers=HEADERS_CLIENT, timeout=TIMEOUT)
    resp.raise_for_status()
    orders = resp.json()
    for order in orders:
        if 'bid' in order and order['bid'] == bid_id:
            return order
    resp = requests.get(url, headers=HEADERS_VENDOR, timeout=TIMEOUT)
    resp.raise_for_status()
    orders = resp.json()
    for order in orders:
        if 'bid' in order and order['bid'] == bid_id:
            return order
    if orders:
        return orders[0]
    raise Exception("Order not found for bid")

def post_production_update(order_id, stage, note):
    url = f"{BASE_URL}/api/v1/orders/{order_id}/production-updates/"
    json_data = {"stage": stage, "note": note}
    resp = requests.post(url, headers=HEADERS_VENDOR, json=json_data, timeout=TIMEOUT)
    return resp

def delete_design_request(request_id):
    url = f"{BASE_URL}/api/v1/requests/{request_id}/"
    return requests.delete(url, headers=HEADERS_CLIENT, timeout=TIMEOUT)

def test_order_production_update_is_forward_only():
    order_id = None
    design_request_id = None
    bid_id = None
    try:
        design_request = create_design_request()
        design_request_id = design_request["id"]
        upload_reference_image(design_request_id)
        create_vendor_profile()
        bid = place_bid(design_request_id)
        bid_id = bid["id"]
        accept_bid(bid_id)
        orders = requests.get(f"{BASE_URL}/api/v1/orders/", headers=HEADERS_CLIENT, timeout=TIMEOUT)
        orders.raise_for_status()
        order = next((o for o in orders.json() if o.get("bid") == bid_id), None)
        if not order:
            orders = requests.get(f"{BASE_URL}/api/v1/orders/", headers=HEADERS_VENDOR, timeout=TIMEOUT)
            orders.raise_for_status()
            order = next((o for o in orders.json() if o.get("bid") == bid_id), None)
        assert order is not None, "Order not found after bid acceptance"
        order_id = order["id"]

        resp = post_production_update(order_id, "cutting", "Cutting stage started")
        assert resp.status_code == 201, f"Expected 201 but got {resp.status_code} with body {resp.text}"
        production_update = resp.json()
        assert production_update["stage"] == "cutting"

        resp_back = post_production_update(order_id, "sourcing", "Trying to revert to sourcing stage")
        assert resp_back.status_code == 400, f"Expected 400 but got {resp_back.status_code} with body {resp_back.text}"
        
    finally:
        if design_request_id:
            try:
                resp_del = delete_design_request(design_request_id)
                assert resp_del.status_code in (204, 404)
            except Exception:
                pass

test_order_production_update_is_forward_only()
