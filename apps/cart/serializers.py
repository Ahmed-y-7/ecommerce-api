from rest_framework import serializers

from apps.products.models import Product
from apps.products.serializers import ProductSerializer

from .models import Cart, CartItem


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.filter(is_active=True),
        source="product",
        write_only=True,
    )
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ("id", "product", "product_id", "quantity", "subtotal")

    def validate(self, attrs):
        product = attrs.get("product") or (self.instance and self.instance.product)
        quantity = attrs.get("quantity", self.instance.quantity if self.instance else 1)
        if product and quantity > product.stock:
            raise serializers.ValidationError(
                f"Only {product.stock} unit(s) of '{product.name}' in stock."
            )
        return attrs


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Cart
        fields = ("id", "items", "total", "updated_at")
