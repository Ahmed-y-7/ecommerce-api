from django.contrib import admin

from .models import Coupon


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        "code", "discount_type", "value", "min_order_total",
        "used_count", "max_uses", "is_active", "valid_until",
    )
    list_filter = ("discount_type", "is_active")
    search_fields = ("code",)
