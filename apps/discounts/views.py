from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.cart.models import Cart

from .models import Coupon
from .serializers import CouponSerializer, ValidateCouponSerializer


class ValidateCouponView(APIView):
    """POST {"code": "SUMMER10"} -> coupon details + discount against current cart."""

    @extend_schema(request=ValidateCouponSerializer, responses={200: dict})
    def post(self, request):
        serializer = ValidateCouponSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data["code"].strip().upper()

        coupon = Coupon.objects.filter(code=code).first()
        if not coupon:
            return Response(
                {"detail": "Unknown coupon code."}, status=status.HTTP_404_NOT_FOUND
            )

        cart = Cart.objects.filter(user=request.user).first()
        subtotal = cart.total if cart else None

        ok, reason = coupon.is_valid(subtotal=subtotal)
        if not ok:
            return Response({"detail": reason}, status=status.HTTP_400_BAD_REQUEST)

        data = CouponSerializer(coupon).data
        if subtotal is not None:
            data["cart_subtotal"] = str(subtotal)
            data["discount"] = str(coupon.discount_for(subtotal))
        return Response(data)
