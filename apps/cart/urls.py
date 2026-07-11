from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import CartItemViewSet, CartView

router = DefaultRouter()
router.register("items", CartItemViewSet, basename="cart-items")

urlpatterns = [
    path("", CartView.as_view(), name="cart"),
    *router.urls,
]
