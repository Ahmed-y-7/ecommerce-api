import pytest

from apps.orders.models import Order


@pytest.mark.django_db
def test_full_checkout_flow(auth_client, product):
    # Add to cart
    resp = auth_client.post(
        "/api/cart/items/", {"product_id": product.id, "quantity": 2}
    )
    assert resp.status_code == 201

    # Cart shows the item and total
    resp = auth_client.get("/api/cart/")
    assert resp.status_code == 200
    assert len(resp.data["items"]) == 1

    # Checkout
    resp = auth_client.post(
        "/api/orders/checkout/", {"shipping_address": "1 Main St, Cairo"}
    )
    assert resp.status_code == 201
    order = Order.objects.get(pk=resp.data["id"])
    assert str(order.total) == "1999.98"

    # Stock deducted, cart cleared
    product.refresh_from_db()
    assert product.stock == 3
    resp = auth_client.get("/api/cart/")
    assert resp.data["items"] == []


@pytest.mark.django_db
def test_cannot_add_more_than_stock(auth_client, product):
    resp = auth_client.post(
        "/api/cart/items/", {"product_id": product.id, "quantity": 99}
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_checkout_empty_cart(auth_client):
    resp = auth_client.post(
        "/api/orders/checkout/", {"shipping_address": "1 Main St"}
    )
    assert resp.status_code == 400
