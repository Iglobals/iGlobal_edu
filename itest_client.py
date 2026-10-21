"""
Thin HTTP client for iTest's exam-access webhook - tells iTest to grant a
buyer access to the JUPEB exams bundled with a book they paid for here.

Contract (iTest implements the receiver):
    POST {ITEST_BASE_URL}/api/webhooks/igs/exam-access
    Content-Type: application/json
    X-IGS-Timestamp: <unix seconds>
    X-IGS-Signature: hex HMAC-SHA256(key=ITEST_WEBHOOK_SECRET,
                                     msg=f"{timestamp}.".encode() + raw_body)
    body: {"event_id", "action": "grant", "email", "full_name", "exam_keys",
           "reference", "book_id", "book_title"}
    200 {"success": true, "granted": [...], "unknown_keys": [...]}
    401 bad signature / stale timestamp, 400 bad payload.

ITEST_WEBHOOK_SECRET here must equal iTest's IGS_WEBHOOK_SECRET.
event_id is stable per payment, so retries are safe (iTest dedupes on it).
Any non-2xx or network error raises ITestError; callers record it and retry
later via payments.retry_pending_exam_grants().
"""
import hashlib
import hmac
import json
import logging
import time

import requests
from flask import current_app

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 15
EXAM_ACCESS_PATH = '/api/webhooks/igs/exam-access'
MY_EXAMS_PATH = '/dashboard/my-exams'


class ITestError(Exception):
    pass


class ITestNotConfigured(ITestError):
    pass


def is_configured() -> bool:
    return bool(current_app.config.get('ITEST_BASE_URL') and current_app.config.get('ITEST_WEBHOOK_SECRET'))


def my_exams_url():
    base = (current_app.config.get('ITEST_BASE_URL') or '').rstrip('/')
    return f'{base}{MY_EXAMS_PATH}' if base else None


def sign(secret: str, timestamp: str, raw_body: bytes) -> str:
    return hmac.new(secret.encode(), f'{timestamp}.'.encode() + raw_body, hashlib.sha256).hexdigest()


def grant_exam_access(*, event_id, email, full_name, exam_keys, reference, book_id, book_title,
                      timeout=DEFAULT_TIMEOUT) -> dict:
    """POST a signed 'grant' event to iTest. Returns iTest's JSON on 2xx,
    raises ITestNotConfigured / ITestError otherwise."""
    base_url = (current_app.config.get('ITEST_BASE_URL') or '').rstrip('/')
    secret = current_app.config.get('ITEST_WEBHOOK_SECRET') or ''
    if not base_url or not secret:
        raise ITestNotConfigured('ITEST_BASE_URL / ITEST_WEBHOOK_SECRET not configured')

    body = {
        'event_id': event_id,
        'action': 'grant',
        'email': (email or '').strip().lower(),
        'full_name': full_name or '',
        'exam_keys': list(exam_keys or []),
        'reference': reference,
        'book_id': int(book_id),
        'book_title': book_title or '',
    }
    # Serialize ONCE and sign exactly the bytes that go on the wire.
    raw_body = json.dumps(body, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    timestamp = str(int(time.time()))
    headers = {
        'Content-Type': 'application/json',
        'X-IGS-Timestamp': timestamp,
        'X-IGS-Signature': sign(secret, timestamp, raw_body),
    }

    try:
        resp = requests.post(f'{base_url}{EXAM_ACCESS_PATH}', data=raw_body, headers=headers, timeout=timeout)
    except requests.RequestException as exc:
        logger.error('iTest exam grant failed for event_id=%s: %s', event_id, exc)
        raise ITestError(f'network error: {exc}') from exc

    try:
        payload = resp.json()
    except ValueError:
        payload = {}

    if not (200 <= resp.status_code < 300):
        msg = payload.get('message') or payload.get('error') or (resp.text or '')[:300]
        logger.error('iTest exam grant returned %s for event_id=%s: %s', resp.status_code, event_id, msg)
        raise ITestError(f'HTTP {resp.status_code}: {msg}')
    if payload.get('success') is False:
        raise ITestError(f"iTest returned success=false: {payload.get('message') or payload.get('error') or ''}")

    if payload.get('unknown_keys'):
        logger.warning('iTest did not recognise exam keys %s for event_id=%s', payload['unknown_keys'], event_id)
    return payload
