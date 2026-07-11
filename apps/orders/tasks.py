from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings


@shared_task
def send_order_confirmation_email(order_id):
    from .models import Order

    order = Order.objects.select_related("user").get(pk=order_id)
    send_mail(
        subject=f"Order #{order.pk} confirmed",
        message=(
            f"Hi {order.user.first_name or order.user.email},\n\n"
            f"Your order #{order.pk} for {order.total} was received "
            f"and is now '{order.status}'.\n\nThanks for shopping with us!"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.user.email],
        fail_silently=False,
    )
    return order_id
