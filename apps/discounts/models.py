from decimal import Decimal

from django.db import models
from django.utils import timezone


class Coupon(models.Model):
    class Type(models.TextChoices):
        PERCENTAGE = "percentage", "Percentage"
        FIXED = "fixed", "Fixed amount"

    code = models.CharField(max_length=40, unique=True)
    discount_type = models.CharField(
        max_length=20, choices=Type.choices, default=Type.PERCENTAGE
    )
    value = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text="Percent (e.g. 10 = 10%) or fixed amount, depending on type.",
    )
    min_order_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    max_uses = models.PositiveIntegerField(default=0, help_text="0 = unlimited")
    used_count = models.PositiveIntegerField(default=0)
    valid_from = models.DateTimeField(default=timezone.now)
    valid_until = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        self.code = self.code.strip().upper()
        super().save(*args, **kwargs)

    def is_valid(self, subtotal=None):
        """Return (ok: bool, reason: str)."""
        now = timezone.now()
        if not self.is_active:
            return False, "This coupon is inactive."
        if self.valid_from and now < self.valid_from:
            return False, "This coupon is not active yet."
        if self.valid_until and now > self.valid_until:
            return False, "This coupon has expired."
        if self.max_uses and self.used_count >= self.max_uses:
            return False, "This coupon has reached its usage limit."
        if subtotal is not None and subtotal < self.min_order_total:
            return False, f"Order total must be at least {self.min_order_total}."
        return True, ""

    def discount_for(self, subtotal):
        if self.discount_type == self.Type.PERCENTAGE:
            discount = subtotal * self.value / Decimal("100")
        else:
            discount = self.value
        return min(discount, subtotal).quantize(Decimal("0.01"))

    def __str__(self):
        return self.code
