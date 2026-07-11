from decimal import Decimal

import pytest
from django.utils import timezone

from apps.discounts.models import Coupon
from apps.orders.models import Order


@pytest.fixture
def coupon(db):
    return Coupon.objects.create(
        code="SAVE10", discount_type=Coupon.Type.PERCENTAGE, value=10
    )


@pytest.mark.django_db
def test_validate_coupon(auth_client, coupon, product):
    auth_client.post("/api/cart/items/", {"product_id": product.id, "quantity": 1})
    resp = auth_client.post("/api/discounts/validate/", {"code": "save10"})
    assert resp.status_code == 200
    assert resp.data["discount"] == "100.00"  # 10% of 999.99 -> 100.00


@pytest.mark.django_db
def test_checkout_with_percentage_coupon(auth_client, coupon, product):
    auth_client.post("/api/cart/items/", {"product_id": product.id, "quantity": 2})
    resp = auth_client.post(
        "/api/orders/checkout/",
        {"shipping_address": "1 Main St", "coupon_code": "SAVE10"},
    )
    assert resp.status_code == 201
    order = Order.objects.get(pk=resp.data["id"])
    assert order.subtotal == Decimal("1999.98")
    assert order.discount_amount == Decimal("200.00")
    assert order.total == Decimal("1799.98")
    coupon.refresh_from_db()
    assert coupon.used_count == 1


@pytest.mark.django_db
def test_checkout_with_expired_coupon(auth_client, coupon, product):
    coupon.valid_until = timezone.now() - timezone.timedelta(days=1)
    coupon.save()
    auth_client.post("/api/cart/items/", {"product_id": product.id, "quantity": 1})
    resp = auth_client.post(
        "/api/orders/checkout/",
        {"shipping_address": "1 Main St", "coupon_code": "SAVE10"},
    )
    assert resp.status_code == 400
    assert "expired" in resp.data["detail"]


@pytest.mark.django_db
def test_fixed_coupon_capped_at_subtotal(db):
    c = Coupon.objects.create(
        code="BIG", discount_type=Coupon.Type.FIXED, value=Decimal("5000")
    )
    assert c.discount_for(Decimal("100.00")) == Decimal("100.00")
