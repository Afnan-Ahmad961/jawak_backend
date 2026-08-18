import io
import requests

BASE_URL = "http://localhost:8000"
VENDOR_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzg3MDY3MzkwLCJpYXQiOjE3ODcwNjM3OTAsImp0aSI6IjE0NDYxMzJhYTE4ZTRmNjViN2EwOWUyZmFkODJkNzE4IiwidXNlcl9pZCI6IjE3In0.5FVPQhzxGnSyQrK3qGZR9gPlLE5EeRRAdppJzKz9ZZ4"
HEADERS = {
    "Authorization": f"Bearer {VENDOR_TOKEN}"
}
TIMEOUT = 30


def test_vendor_portfolio_create_list_delete():
    # Create a small in-memory PNG file
    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x05\x00\x00\x00\x05"
        b"\x08\x02\x00\x00\x00\x02\x50\x58\xea\x00\x00\x00\x0cIDAT\x08\xd7c\xf8"
        b"\xcf\xc0\x00\x00\x03\x01\x01\x00\x18\xdd\x18\xc9\x00\x00\x00\x00IEND"
        b"\xaeB`\x82"
    )
    file_obj = io.BytesIO(png_bytes)
    file_obj.name = "test.png"

    portfolio_create_url = f"{BASE_URL}/api/v1/vendors/me/portfolio/"
    portfolio_list_url = portfolio_create_url  # same url for GET
    try:
        # POST to create portfolio item
        files = {
            "image": ("test.png", file_obj, "image/png"),
        }
        data = {
            "title": "Test Portfolio Item",
            "description": "Test description for portfolio item"
        }
        response = requests.post(
            portfolio_create_url,
            headers=HEADERS,
            files=files,
            data=data,
            timeout=TIMEOUT
        )
        assert response.status_code == 201, f"Expected 201 Created, got {response.status_code}"
        portfolio_item = response.json()
        assert "id" in portfolio_item, "Response JSON missing 'id'"
        assert portfolio_item.get("title") == data["title"], "Title mismatch in response"

        item_id = portfolio_item["id"]

        # GET to list portfolio items and verify created item present
        response = requests.get(
            portfolio_list_url,
            headers=HEADERS,
            timeout=TIMEOUT
        )
        assert response.status_code == 200, f"Expected 200 OK on list, got {response.status_code}"
        items = response.json()
        assert isinstance(items, list), "Portfolio list response is not a list"
        assert any(item.get("id") == item_id for item in items), "Created portfolio item not found in list"

    finally:
        # DELETE the created portfolio item
        if 'item_id' in locals():
            delete_url = f"{BASE_URL}/api/v1/vendors/me/portfolio/{item_id}/"
            del_response = requests.delete(
                delete_url,
                headers=HEADERS,
                timeout=TIMEOUT
            )
            assert del_response.status_code == 204, f"Expected 204 No Content on delete, got {del_response.status_code}"


test_vendor_portfolio_create_list_delete()
