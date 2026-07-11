from drf_spectacular.utils import extend_schema
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from .models import Category, Product
from .serializers import (
    CategorySerializer,
    ProductImageSerializer,
    ProductSerializer,
)


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (IsAdminOrReadOnly,)
    lookup_field = "slug"


class ProductViewSet(viewsets.ModelViewSet):
    queryset = (
        Product.objects.select_related("category")
        .prefetch_related("images")
        .filter(is_active=True)
    )
    serializer_class = ProductSerializer
    permission_classes = (IsAdminOrReadOnly,)
    lookup_field = "slug"
    filterset_fields = ("category__slug", "is_active")
    search_fields = ("name", "description")
    ordering_fields = ("price", "created_at", "name")

    @extend_schema(request=ProductImageSerializer, responses={201: ProductImageSerializer})
    @action(
        detail=True,
        methods=["post"],
        parser_classes=[MultiPartParser, FormParser],
        url_path="images",
    )
    def upload_image(self, request, slug=None):
        """Upload an image for this product (staff only, multipart form)."""
        product = self.get_object()
        serializer = ProductImageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(product=product)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
