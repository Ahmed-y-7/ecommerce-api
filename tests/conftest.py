import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from apps.products.models import Category, Product

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(email="buyer@example.com", password="Str0ngPass!123")


@pytest.fixture
def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def product(db):
    category = Category.objects.create(name="Electronics")
    return Product.objects.create(
        category=category, name="Laptop", price="999.99", stock=5
    )
