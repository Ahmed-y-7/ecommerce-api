import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.products.models import ProductImage


def make_image_file():
    buf = io.BytesIO()
    Image.new("RGB", (10, 10), "red").save(buf, format="JPEG")
    buf.seek(0)
    return SimpleUploadedFile("test.jpg", buf.read(), content_type="image/jpeg")


@pytest.mark.django_db
def test_product_serializer_includes_images(auth_client, product):
    ProductImage.objects.create(product=product, image=make_image_file(), alt_text="x")
    resp = auth_client.get(f"/api/products/{product.slug}/")
    assert resp.status_code == 200
    assert len(resp.data["images"]) == 1


@pytest.mark.django_db
def test_non_admin_cannot_upload_image(auth_client, product):
    resp = auth_client.post(
        f"/api/products/{product.slug}/images/",
        {"image": make_image_file()},
        format="multipart",
    )
    assert resp.status_code == 403


@pytest.mark.django_db
def test_admin_can_upload_image(user, product):
    from rest_framework.test import APIClient

    user.is_staff = True
    user.save()
    client = APIClient()
    client.force_authenticate(user=user)
    resp = client.post(
        f"/api/products/{product.slug}/images/",
        {"image": make_image_file()},
        format="multipart",
    )
    assert resp.status_code == 201
    assert product.images.count() == 1
