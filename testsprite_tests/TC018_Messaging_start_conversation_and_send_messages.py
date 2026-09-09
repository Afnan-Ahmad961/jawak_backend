import requests
import datetime

BASE_URL = "http://localhost:8000"
CLIENT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg3MDY3MzkwLCJpYXQiOjE3ODcwNjM3OTAsImp0aSI6IjViNDcxNzYxOGVmNzQyMzFhNmE2NDM4ZGNmNjQ0NzVhIiwidXNlcl9pZCI6IjE2In0.aGPMbcKE9xiFlzgUE1E7-olCQIl-ZCk70LCC-9I2L9E"
VENDOR_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg3MDY3MzkwLCJpYXQiOjE3ODcwNjM3OTAsImp0aSI6IjE0NDYxMzJhYTE4ZTRmNjViN2EwOWUyZmFkODJkNzE4IiwidXNlcl9pZCI6IjE3In0.5FVPQhzxGnSyQrK3qGZR9gPlLE5EeRRAdppJzKz9ZZ4"

HEADERS_CLIENT = {
    "Authorization": f"Bearer {CLIENT_TOKEN}",
    "Content-Type": "application/json",
}

HEADERS_VENDOR = {
    "Authorization": f"Bearer {VENDOR_TOKEN}",
    "Content-Type": "application/json",
}

TIMEOUT = 30


def create_design_request():
    url = f"{BASE_URL}/api/v1/requests/"
    today = datetime.date.today()
    deadline = (today + datetime.timedelta(days=10)).isoformat()
    payload = {
        "title": "Test Design Request for Messaging",
        "description": "A test design request created for messaging tests",
        "apparel_type": "hoodie",
        "quantity": 10,
        "material": "cotton",
        "sizes": ["M", "L"],
        "color_preferences": "blue and black",
        "deadline": deadline,
    }
    resp = requests.post(url, headers=HEADERS_CLIENT, json=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    assert resp.status_code == 201
    return resp.json()["id"]


def create_vendor_profile():
    # Update own vendor profile to create vendor record (PUT)
    url = f"{BASE_URL}/api/v1/vendors/me/"
    payload = {
        "company_name": "Test Vendor Company",
        "location": "Test Location",
        "specialties": ["hoodies", "jackets"],
        "capacity": 100,
    }
    resp = requests.put(url, headers=HEADERS_VENDOR, json=payload, timeout=TIMEOUT)
    resp.raise_for_status()
    assert resp.status_code == 200
    vendor = resp.json()
    vendor_id = vendor.get("id")
    assert vendor_id is not None
    return vendor_id


def test_tc018_messaging_start_conversation_and_send_messages():
    # Create prerequisite design request and vendor profile
    design_request_id = None
    vendor_id = None
    conversation_id = None
    try:
        design_request_id = create_design_request()
        vendor_id = create_vendor_profile()

        # Start a conversation (CLIENT)
        url_conversations = f"{BASE_URL}/api/v1/conversations/"
        payload_conversation = {
            "design_request": design_request_id,
            "vendor": vendor_id,
        }
        resp = requests.post(url_conversations, headers=HEADERS_CLIENT, json=payload_conversation, timeout=TIMEOUT)
        resp.raise_for_status()
        assert resp.status_code == 201
        conversation = resp.json()
        conversation_id = conversation.get("id")
        assert conversation_id is not None

        # Send a message to the conversation (CLIENT)
        url_messages = f"{BASE_URL}/api/v1/conversations/{conversation_id}/messages/"
        payload_message = {"body": "Hello"}
        resp = requests.post(url_messages, headers=HEADERS_CLIENT, json=payload_message, timeout=TIMEOUT)
        resp.raise_for_status()
        assert resp.status_code == 201
        message = resp.json()
        assert message.get("body") == "Hello"

        # Retrieve messages for the conversation (CLIENT)
        resp = requests.get(url_messages, headers=HEADERS_CLIENT, timeout=TIMEOUT)
        resp.raise_for_status()
        assert resp.status_code == 200
        messages = resp.json()
        assert isinstance(messages, list)
        assert any(msg.get("body") == "Hello" for msg in messages)

    finally:
        # Cleanup: delete the conversation? API does not specify delete for conversation.
        # Cleanup: delete design request to not pollute data
        if design_request_id:
            try:
                url_del = f"{BASE_URL}/api/v1/requests/{design_request_id}/"
                del_resp = requests.delete(url_del, headers=HEADERS_CLIENT, timeout=TIMEOUT)
                if del_resp.status_code not in (204, 404):
                    del_resp.raise_for_status()
            except Exception:
                pass
        # Vendor profile cleanup not defined; assume idempotent for test user

test_tc018_messaging_start_conversation_and_send_messages()
