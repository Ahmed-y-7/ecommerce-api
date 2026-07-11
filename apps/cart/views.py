from rest_framework import generics, mixins, status, viewsets
from rest_framework.response import Response

from .models import Cart, CartItem
from .serializers import CartItemSerializer, CartSerializer


def get_user_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


class CartView(generics.RetrieveDestroyAPIView):
    """GET /api/cart/ - view cart. DELETE - clear cart."""

    serializer_class = CartSerializer

    def get_object(self):
        return get_user_cart(self.request.user)

    def perform_destroy(self, instance):
        instance.items.all().delete()


class CartItemViewSet(
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = CartItemSerializer

    def get_queryset(self):
        return CartItem.objects.filter(cart__user=self.request.user)

    def create(self, request, *args, **kwargs):
        """Add product to cart; if already present, increase quantity."""
        cart = get_user_cart(request.user)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.validated_data["product"]
        quantity = serializer.validated_data.get("quantity", 1)
        item, created = CartItem.objects.get_or_create(
            cart=cart, product=product, defaults={"quantity": quantity}
        )
        if not created:
            item.quantity += quantity
            item.save()
        out = self.get_serializer(item)
        return Response(out.data, status=status.HTTP_201_CREATED)
