from rest_framework import serializers

from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ("id", "product", "product_name", "price", "quantity", "subtotal")


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    coupon_code = serializers.CharField(source="coupon.code", read_only=True, default=None)

    class Meta:
        model = Order
        fields = (
            "id", "status", "subtotal", "coupon_code", "discount_amount", "total",
            "shipping_address", "items", "created_at", "updated_at",
        )
        read_only_fields = (
            "status", "subtotal", "discount_amount", "total", "created_at", "updated_at",
        )


class CheckoutSerializer(serializers.Serializer):
    shipping_address = serializers.CharField()
    coupon_code = serializers.CharField(required=False, allow_blank=True)
