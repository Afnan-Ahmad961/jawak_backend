import requests
import datetime

BASE_URL = "http://localhost:8000"
CLIENT_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg3MDY3MzkwLCJpYXQiOjE3ODcwNjM3OTAsImp0aSI6IjViNDcxNzYxOGVmNzQyMzFhNmE2NDM4ZGNmNjQ0NzVhIiwidXNlcl9pZCI6IjE2In0.aGPMbcKE9xiFlzgUE1E7-olCQIl-ZCk70LCC-9I2L9E"

HEADERS = {
    "Authorization": f"Bearer {CLIENT_TOKEN}",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def test_list_and_retrieve_design_requests():
    session = requests.Session()
    session.headers.update(HEADERS)
    timeout = 30

    request_id = None
    # Step 1: GET /api/v1/requests/ to list design requests scoped by the client
    list_url = f"{BASE_URL}/api/v1/requests/"
    try:
        resp_list = session.get(list_url, timeout=timeout)
        assert resp_list.status_code == 200, f"Expected 200, got {resp_list.status_code}"
        requests_list = resp_list.json()
        assert isinstance(requests_list, list), "Expected list of requests"

        # If client has any existing requests, pick the first one
        if requests_list:
            request_item = requests_list[0]
            assert "id" in request_item, "Request item missing 'id'"
            request_id = request_item["id"]
        else:
            # No existing requests, create one
            create_url = f"{BASE_URL}/api/v1/requests/"
            deadline_str = (datetime.datetime.utcnow() + datetime.timedelta(days=30)).date().isoformat()
            payload = {
                "title": "Test Design Request for TC007",
                "description": "Test description for design request",
                "apparel_type": "hoodie",
                "quantity": 100,
                "material": "cotton",
                "sizes": [{"size": "M", "quantity": 50}, {"size": "L", "quantity": 50}],
                "color_preferences": "blue and white",
                "deadline": deadline_str
            }

            resp_create = session.post(create_url, json=payload, timeout=timeout)
            assert resp_create.status_code == 201, f"Expected 201 on create, got {resp_create.status_code}"
            created_request = resp_create.json()
            assert "id" in created_request, "Created request missing 'id'"
            assert created_request.get("status", "").lower() == "open" or "status" in created_request, "Created request missing or wrong status"
            request_id = created_request["id"]

        # Step 2: GET /api/v1/requests/{request_id}/ to retrieve the design request details
        retrieve_url = f"{BASE_URL}/api/v1/requests/{request_id}/"
        resp_retrieve = session.get(retrieve_url, timeout=timeout)
        assert resp_retrieve.status_code == 200, f"Expected 200 on retrieval, got {resp_retrieve.status_code}"
        retrieved_data = resp_retrieve.json()
        assert isinstance(retrieved_data, dict), "Retrieved data is not a dict"
        assert retrieved_data.get("id") == request_id, "Retrieved request id does not match"

        # Step 3: GET /api/v1/requests/{non_existent_id}/ should return 404
        non_existent_id = 999999999
        if request_id == non_existent_id:
            non_existent_id += 1  # avoid clash if created id is huge
        non_exist_url = f"{BASE_URL}/api/v1/requests/{non_existent_id}/"
        resp_404 = session.get(non_exist_url, timeout=timeout)
        assert resp_404.status_code == 404, f"Expected 404 for non-existent id, got {resp_404.status_code}"

    finally:
        # Cleanup: delete the created request if created during this test
        if request_id is not None:
            # We only want to delete if we created it ourselves (i.e. if no requests initially)
            if not requests_list or (requests_list and not any(r["id"] == request_id for r in requests_list)):
                delete_url = f"{BASE_URL}/api/v1/requests/{request_id}/"
                del_resp = session.delete(delete_url, timeout=timeout)
                # Accept 204 No Content or 200 OK as deletion success
                assert del_resp.status_code in (200, 204), f"Cleanup deletion failed with {del_resp.status_code}"

test_list_and_retrieve_design_requests()