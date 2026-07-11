import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_product_list_is_public(product):
    resp = APIClient().get("/api/products/")
    assert resp.status_code == 200
    assert resp.data["count"] == 1
    assert resp.data["results"][0]["name"] == "Laptop"


@pytest.mark.django_db
def test_only_admin_can_create_product(auth_client, product):
    resp = auth_client.post(
        "/api/products/",
        {"name": "Phone", "price": "10.00", "stock": 1,
         "category_id": product.category_id},
    )
    assert resp.status_code == 403
