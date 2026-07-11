import stripe
from django.conf import settings
from drf_spectacular.utils import extend_schema
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.orders.models import Order

from .models import Payment

stripe.api_key = settings.STRIPE_SECRET_KEY


class CreateIntentSerializer(serializers.Serializer):
    order_id = serializers.IntegerField()


class CreatePaymentIntentView(APIView):
    """POST {"order_id": 1} -> Stripe PaymentIntent client_secret."""

    @extend_schema(request=CreateIntentSerializer, responses={200: dict})
    def post(self, request):
        serializer = CreateIntentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order_id = serializer.validated_data["order_id"]
        order = Order.objects.filter(
            pk=order_id, user=request.user, status=Order.Status.PENDING
        ).first()
        if not order:
            return Response(
                {"detail": "Pending order not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        amount_cents = int(order.total * 100)

        if settings.STRIPE_SECRET_KEY:
            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency="usd",
                metadata={"order_id": order.pk},
                automatic_payment_methods={
                    "enabled": True,
                    "allow_redirects": "never",
                },
            )
            intent_id, client_secret = intent.id, intent.client_secret
        else:
            # Stub mode - no Stripe key configured
            intent_id = f"pi_stub_{order.pk}"
            client_secret = f"{intent_id}_secret_stub"

        Payment.objects.update_or_create(
            order=order,
            defaults={
                "stripe_payment_intent_id": intent_id,
                "amount": order.total,
                "status": Payment.Status.PENDING,
            },
        )
        return Response({"client_secret": client_secret, "payment_intent": intent_id})


class StripeWebhookView(APIView):
    """Receives Stripe events. Configure endpoint in the Stripe dashboard."""

    authentication_classes = ()
    permission_classes = (AllowAny,)

    def post(self, request):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except (ValueError, stripe.error.SignatureVerificationError):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        if event["type"] == "payment_intent.succeeded":
            intent = event["data"]["object"]
            payment = Payment.objects.filter(
                stripe_payment_intent_id=intent["id"]
            ).select_related("order").first()
            if payment:
                payment.status = Payment.Status.SUCCEEDED
                payment.save(update_fields=["status"])
                payment.order.status = Order.Status.PAID
                payment.order.save(update_fields=["status"])

        return Response({"received": True})
