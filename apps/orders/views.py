from decimal import Decimal

from django.db import transaction
from django.db.models import F
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.cart.models import Cart
from apps.discounts.models import Coupon
from apps.products.models import Product

from .models import Order, OrderItem
from .serializers import CheckoutSerializer, OrderSerializer
from .tasks import send_order_confirmation_email


class OrderViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    serializer_class = OrderSerializer

    def get_queryset(self):
        return (
            Order.objects.filter(user=self.request.user)
            .select_related("coupon")
            .prefetch_related("items__product")
        )

    @action(detail=False, methods=["post"])
    def checkout(self, request):
        """Create an order from the user's cart, deduct stock atomically.

        Optionally accepts a coupon_code which is validated and applied.
        """
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cart = Cart.objects.filter(user=request.user).first()
        if not cart or not cart.items.exists():
            return Response(
                {"detail": "Your cart is empty."}, status=status.HTTP_400_BAD_REQUEST
            )

        code = (serializer.validated_data.get("coupon_code") or "").strip().upper()

        with transaction.atomic():
            coupon = None
            if code:
                coupon = (
                    Coupon.objects.select_for_update().filter(code=code).first()
                )
                if not coupon:
                    return Response(
                        {"detail": "Unknown coupon code."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            order = Order.objects.create(
                user=request.user,
                shipping_address=serializer.validated_data["shipping_address"],
            )
            subtotal = Decimal("0")
            for item in cart.items.select_related("product"):
                # Lock the product row to prevent overselling
                product = Product.objects.select_for_update().get(pk=item.product_id)
                if item.quantity > product.stock:
                    return Response(
                        {"detail": f"Insufficient stock for '{product.name}'."},
                        status=status.HTTP_409_CONFLICT,
                    )
                product.stock -= item.quantity
                product.save(update_fields=["stock"])
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    price=product.price,
                    quantity=item.quantity,
                )
                subtotal += product.price * item.quantity

            discount = Decimal("0")
            if coupon:
                ok, reason = coupon.is_valid(subtotal=subtotal)
                if not ok:
                    return Response(
                        {"detail": reason}, status=status.HTTP_400_BAD_REQUEST
                    )
                discount = coupon.discount_for(subtotal)
                coupon.used_count = F("used_count") + 1
                coupon.save(update_fields=["used_count"])
                order.coupon = coupon

            order.subtotal = subtotal
            order.discount_amount = discount
            order.total = subtotal - discount
            order.save(update_fields=["subtotal", "discount_amount", "total", "coupon"])
            cart.items.all().delete()

        send_order_confirmation_email.delay(order.pk)
        return Response(
            OrderSerializer(order).data, status=status.HTTP_201_CREATED
        )
