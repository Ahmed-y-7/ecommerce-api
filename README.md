# E-commerce API (Django + DRF)

Full-featured e-commerce backend: JWT auth, products, cart, orders with atomic
stock deduction, Celery email tasks, Stripe payment stubs, PostgreSQL, Redis.

## Stack
Django 5 · DRF · SimpleJWT · PostgreSQL · Celery + Redis · Stripe · Docker

## Quick start (Docker - recommended)
```bash
cp .env.example .env
docker compose up --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```
API: http://localhost:8000/api/docs/ (Swagger UI)

## Quick start (local)
Requires PostgreSQL and Redis running (see .env for connection settings).
```bash
python -m venv venv && venv\Scripts\activate   # Windows
pip install -r requirements.txt
cp .env.example .env
python manage.py makemigrations && python manage.py migrate
python manage.py runserver
# In a second terminal:
celery -A config worker -l info
```

## Endpoints
| Method | URL | Description |
|---|---|---|
| POST | /api/auth/register/ | Create account |
| POST | /api/auth/token/ | Get JWT (email + password) |
| POST | /api/auth/token/refresh/ | Refresh token |
| GET/PATCH | /api/auth/me/ | Profile |
| GET | /api/products/ | List (search, filter, ordering, pagination) |
| CRUD | /api/products/categories/ | Categories (admin write) |
| GET/DELETE | /api/cart/ | View / clear cart |
| POST | /api/cart/items/ | Add item `{product_id, quantity}` |
| PATCH/DELETE | /api/cart/items/{id}/ | Update / remove item |
| GET | /api/orders/ | My orders |
| POST | /api/orders/checkout/ | Cart -> order `{shipping_address, coupon_code?}` |
| POST | /api/payments/create-intent/ | Stripe PaymentIntent `{order_id}` |
| POST | /api/payments/webhook/ | Stripe webhook |
| POST | /api/discounts/validate/ | Preview coupon against cart `{code}` |
| POST | /api/products/{slug}/images/ | Upload product image (staff, multipart) |

## Tests
```bash
pytest
```
Tests use SQLite in-memory + eager Celery, so no services are needed.
