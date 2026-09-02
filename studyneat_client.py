"""
Thin HTTP client for StudyNeat's partner SSO endpoint.

Deliberately on-demand only, per the actual agreed design: iGlobal_edu is the
sole source of truth for book ownership and subscription status - StudyNeat
is never proactively told what a user owns. This is called exactly once, at
the moment a subscribed user clicks "Use AI Deep Dive" on a book they own; if
their session there later expires, they just click the button again to get a
fresh token. No sync, no caching, no background jobs.
"""
import logging

import requests
from flask import current_app

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 15


class StudyNeatError(Exception):
    pass


def create_sso_session(email: str, name: str, book_id: str) -> str:
    """POSTs to StudyNeat's partner SSO endpoint and returns the redirectUrl
    to send the user's browser to. Raises StudyNeatError on any failure -
    callers should show a friendly error rather than a raw 500."""
    base_url = current_app.config.get('STUDYNEAT_API_BASE_URL', 'https://api.studyneat.xyz')
    client_key = current_app.config.get('STUDYNEAT_CLIENT_KEY', '')
    client_secret = current_app.config.get('STUDYNEAT_CLIENT_SECRET', '')

    try:
        resp = requests.post(
            f"{base_url}/api/partner/sso/session",
            headers={
                "Content-Type": "application/json",
                "x-client-key": client_key,
                "x-client-secret": client_secret,
            },
            json={"email": email, "name": name, "bookId": book_id},
            timeout=DEFAULT_TIMEOUT,
        )
        payload = resp.json()
    except requests.RequestException as exc:
        logger.error("StudyNeat SSO call failed for book_id=%s: %s", book_id, exc)
        raise StudyNeatError(str(exc)) from exc

    if not resp.ok or not payload.get("success") or not payload.get("redirectUrl"):
        logger.error("StudyNeat SSO call returned an error for book_id=%s: %s", book_id, payload)
        raise StudyNeatError(payload.get("message", "StudyNeat did not return a redirect URL"))

    return payload["redirectUrl"]
