from rest_framework import serializers

from .models import Coupon


class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = ("code", "discount_type", "value", "min_order_total")


class ValidateCouponSerializer(serializers.Serializer):
    code = serializers.CharField()
