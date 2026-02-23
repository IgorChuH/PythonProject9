import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

def create_stripe_product(name, description=None):
    """
    Создание продукта в Stripe.
    Возвращает ID продукта.
    """
    product = stripe.Product.create(
        name=name,
        description=description,
    )
    return product.id

def create_stripe_price(product_id, amount, currency='rub'):
    """
    Создание цены для продукта.
    amount - в рублях (или валюте), будет умножено на 100.
    Возвращает ID цены.
    """
    price = stripe.Price.create(
        product=product_id,
        unit_amount=int(amount * 100),  # в копейках
        currency=currency,
    )
    return price.id

def create_stripe_checkout_session(price_id, success_url, cancel_url):
    """
    Создание сессии для оплаты.
    Возвращает (session_id, payment_url).
    """
    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=[{
            'price': price_id,
            'quantity': 1,
        }],
        mode='payment',
        success_url=success_url,
        cancel_url=cancel_url,
    )
    return session.id, session.url

def retrieve_stripe_session(session_id):
    """
    Получение информации о сессии (статус и т.д.)
    """
    return stripe.checkout.Session.retrieve(session_id)