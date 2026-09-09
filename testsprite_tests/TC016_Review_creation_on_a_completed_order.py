import requests
import uuid
import datetime

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

def create_design_request():
    url = f"{BASE_URL}/api/v1/requests/"
    deadline = (datetime.date.today() + datetime.timedelta(days=30)).isoformat()
    payload = {
        "title": "Test Hoodie " + str(uuid.uuid4()),
        "description": "Test description",
        "apparel_type": "hoodie",
        "quantity": 10,
        "material": "cotton",
        "sizes": ["M", "L"],
        "color_preferences": "blue",
        "deadline": deadline
    }
    resp = requests.post(url, json=payload, headers=HEADERS_CLIENT, timeout=30)
    resp.raise_for_status()
    return resp.json()["id"]

def place_bid(design_request_id):
    url = f"{BASE_URL}/api/v1/bids/"
    payload = {
        "design_request": design_request_id,
        "proposed_price": 1000,
        "delivery_days": 15,
        "message": "I can do this"
    }
    resp = requests.post(url, json=payload, headers=HEADERS_VENDOR, timeout=30)
    resp.raise_for_status()
    return resp.json()["id"]

def accept_bid(bid_id):
    url = f"{BASE_URL}/api/v1/bids/{bid_id}/status/"
    payload = {"status": "accepted"}
    resp = requests.patch(url, json=payload, headers=HEADERS_CLIENT, timeout=30)
    resp.raise_for_status()
    return resp.json()

def get_orders():
    url = f"{BASE_URL}/api/v1/orders/"
    resp = requests.get(url, headers=HEADERS_CLIENT, timeout=30)
    resp.raise_for_status()
    return resp.json()

def confirm_order_delivery(order_id):
    url = f"{BASE_URL}/api/v1/orders/{order_id}/confirm-delivery/"
    resp = requests.post(url, headers=HEADERS_CLIENT, timeout=30)
    resp.raise_for_status()
    return resp.json()

def post_review(order_id, rating, comment):
    url = f"{BASE_URL}/api/v1/reviews/"
    payload = {
        "order": order_id,
        "rating": rating,
        "comment": comment
    }
    resp = requests.post(url, json=payload, headers=HEADERS_CLIENT, timeout=30)
    return resp

def test_review_creation_on_completed_order():
    # Create design request by client
    design_request_id = create_design_request()

    # Vendor places bid
    bid_id = place_bid(design_request_id)

    # Client accepts bid to create order
    bid_data = accept_bid(bid_id)
    # Confirm returned bid data includes id and status
    assert bid_data.get("id") == bid_id
    assert bid_data.get("status") == "accepted"

    # Retrieve orders and find order related to this bid
    orders = get_orders()
    order_id = None
    for order in orders:
        # The PRD doesn't specify order model details here, assuming order has 'bid' or 'bid_id' relation
        # but since we don't have that, fallback to first order for this test
        order_id = order.get("id")
        if order_id is not None:
            break
    assert order_id is not None, "Order ID should be present after bid acceptance"

    # Confirm delivery to complete order
    confirm_resp = confirm_order_delivery(order_id)
    assert confirm_resp.get("status") == "completed", "Order should be in completed status"

    comment_1 = "Excellent work, very satisfied."
    # Post first review (valid)
    resp1 = post_review(order_id, rating=5, comment=comment_1)
    assert resp1.status_code == 201, f"Expected 201 for first review, got {resp1.status_code}"
    review1 = resp1.json()
    assert review1.get("order") == order_id
    assert review1.get("rating") == 5
    assert review1.get("comment") == comment_1

    # Post second review from same reviewer (should be 400)
    resp2 = post_review(order_id, rating=4, comment="Second review attempt")
    assert resp2.status_code == 400, f"Expected 400 for duplicate review, got {resp2.status_code}"

    # Post review with invalid rating (0, below 1)
    resp3 = post_review(order_id, rating=0, comment="Invalid rating below range")
    assert resp3.status_code == 400, f"Expected 400 for rating below range, got {resp3.status_code}"

    # Post review with invalid rating (6, above 5)
    resp4 = post_review(order_id, rating=6, comment="Invalid rating above range")
    assert resp4.status_code == 400, f"Expected 400 for rating above range, got {resp4.status_code}"


test_review_creation_on_completed_order()
