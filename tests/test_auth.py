import pytest
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_register_and_login():
    client = APIClient()
    resp = client.post(
        "/api/auth/register/",
        {"email": "new@example.com", "password": "Str0ngPass!123"},
    )
    assert resp.status_code == 201

    resp = client.post(
        "/api/auth/token/",
        {"email": "new@example.com", "password": "Str0ngPass!123"},
    )
    assert resp.status_code == 200
    assert "access" in resp.data


@pytest.mark.django_db
def test_me_requires_auth():
    assert APIClient().get("/api/auth/me/").status_code == 401
