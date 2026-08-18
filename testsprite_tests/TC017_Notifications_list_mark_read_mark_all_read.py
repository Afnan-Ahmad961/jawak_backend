import requests

BASE_URL = "http://localhost:8000"
VENDOR_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg3MDY3MzkwLCJpYXQiOjE3ODcwNjM3OTAsImp0aSI6IjE0NDYxMzJhYTE4ZTRmNjViN2EwOWUyZmFkODJkNzE4IiwidXNlcl9pZCI6IjE3In0.5FVPQhzxGnSyQrK3qGZR9gPlLE5EeRRAdppJzKz9ZZ4"
TIMEOUT = 30

def test_notifications_list_mark_read_mark_all_read():
    headers = {
        "Authorization": f"Bearer {VENDOR_TOKEN}",
        "Accept": "application/json",
    }

    # Step 1: GET /api/v1/notifications/
    notifications_url = f"{BASE_URL}/api/v1/notifications/"
    response = requests.get(notifications_url, headers=headers, timeout=TIMEOUT)
    assert response.status_code == 200, f"GET /notifications/ expected 200, got {response.status_code}"
    notifications = response.json()
    assert isinstance(notifications, list), "Notifications response should be a list"

    # Filter notifications for those with is_read==False if possible, else take any that have is_read field
    notification_to_mark_read = None
    for n in notifications:
        # Pick first notification that is not read or any notification if none unread
        if isinstance(n, dict) and "id" in n and "is_read" in n:
            if not n["is_read"]:
                notification_to_mark_read = n
                break
    if notification_to_mark_read is None and notifications:
        # fallback to first notification with id
        for n in notifications:
            if isinstance(n, dict) and "id" in n:
                notification_to_mark_read = n
                break

    # If no notifications exist, the test cannot proceed meaningfully but assertions should not fail
    if notification_to_mark_read is None:
        # No notification found, but 200 with empty list is valid
        # Still attempt to mark all read endpoint
        read_all_url = f"{BASE_URL}/api/v1/notifications/read-all/"
        resp_read_all = requests.post(read_all_url, headers=headers, timeout=TIMEOUT)
        assert resp_read_all.status_code == 200, f"POST /notifications/read-all/ expected 200, got {resp_read_all.status_code}"
        return

    notification_id = notification_to_mark_read["id"]

    # Step 2: POST /api/v1/notifications/{id}/read/
    mark_read_url = f"{BASE_URL}/api/v1/notifications/{notification_id}/read/"
    response_mark_read = requests.post(mark_read_url, headers=headers, timeout=TIMEOUT)
    assert response_mark_read.status_code == 200, f"POST /notifications/{notification_id}/read/ expected 200, got {response_mark_read.status_code}"
    notification_after_mark = response_mark_read.json()
    assert notification_after_mark.get("id") == notification_id, "Notification ID mismatch after marking read"
    assert notification_after_mark.get("is_read") is True, "Notification is_read flag should be True after marking read"

    # Step 3: POST /api/v1/notifications/read-all/
    read_all_url = f"{BASE_URL}/api/v1/notifications/read-all/"
    response_read_all = requests.post(read_all_url, headers=headers, timeout=TIMEOUT)
    assert response_read_all.status_code == 200, f"POST /notifications/read-all/ expected 200, got {response_read_all.status_code}"

test_notifications_list_mark_read_mark_all_read()