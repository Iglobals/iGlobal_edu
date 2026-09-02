"""
Thin HTTP client for Paystack's recurring-billing endpoints (Plans,
Subscriptions) - separate from the one-off book-purchase calls already made
inline in routes.py's initialize_payment/verify_payment, since those two
payment shapes (one-off vs. recurring) use different Paystack endpoints.

Same PAYSTACK_SECRET_KEY already configured in app.py for book purchases -
no new credential.
"""
import logging

import requests
from flask import current_app

logger = logging.getLogger(__name__)

BASE_URL = "https://api.paystack.co"
DEFAULT_TIMEOUT = 15


class PaystackError(Exception):
    pass


def _headers():
    return {
        "Authorization": f"Bearer {current_app.config.get('PAYSTACK_SECRET_KEY', '')}",
        "Content-Type": "application/json",
    }


def _request(method, path, **kwargs):
    try:
        resp = requests.request(method, f"{BASE_URL}{path}", headers=_headers(), timeout=DEFAULT_TIMEOUT, **kwargs)
        payload = resp.json()
    except requests.RequestException as exc:
        logger.error("Paystack request failed: %s %s - %s", method, path, exc)
        raise PaystackError(str(exc)) from exc

    if not resp.ok or not payload.get("status"):
        message = payload.get("message", "Unknown Paystack error")
        logger.error("Paystack API error: %s %s - %s", method, path, message)
        raise PaystackError(message)

    return payload["data"]


def create_plan(name: str, amount_kobo: int, interval: str) -> dict:
    """`interval` is Paystack's vocabulary: 'monthly' or 'annually'."""
    return _request("POST", "/plan", json={
        "name": name,
        "amount": amount_kobo,
        "interval": interval,
        "currency": "NGN",
    })


def verify_transaction(reference: str) -> dict:
    return _request("GET", f"/transaction/verify/{reference}")


def disable_subscription(subscription_code: str, email_token: str) -> dict:
    return _request("POST", "/subscription/disable", json={
        "code": subscription_code,
        "token": email_token,
    })
