"""
Book / exam-package payment fulfilment - the ONE place a successful Paystack
charge turns into access. Called from:
  - routes.verify_payment            (browser callback after the popup)
  - routes.handle_book_charge_success (legacy direct Paystack webhook)
  - ica_webhook_routes.ica_relay_paystack (purpose 'book_purchase' | 'exam_upgrade')

Both callback and webhook usually fire for the same charge, sometimes at the
same moment, so fulfilment is idempotent: the pending->success flip is a
single conditional UPDATE, and only the caller whose UPDATE actually changed
the row does the follow-up work (library item, referral, iTest grant).

References: book purchases are 'IGS-<purchase.id>-<ts>', exam upgrades are
'IGX-<exam_access_purchase.id>-<ts>'; lookup is by reference against both
tables, so the dispatcher never has to trust metadata to pick the table.
"""
import logging
from datetime import datetime

from extensions import db
from models import Book, ExamAccessPurchase, LibraryItem, Purchase, User, attribute_referral
from exam_packages import PACKAGE_BOOK_EXAM, naira_to_kobo
import itest_client

logger = logging.getLogger(__name__)

# fulfil_charge() result codes
FULFILLED = 'fulfilled'
ALREADY_FULFILLED = 'already_fulfilled'
NOT_FOUND = 'not_found'
NOT_SUCCESS = 'not_success'
AMOUNT_TOO_LOW = 'amount_too_low'


class FulfilResult:
    def __init__(self, status, kind=None, record=None):
        self.status = status          # one of the codes above
        self.kind = kind              # 'purchase' | 'upgrade' | None
        self.record = record          # Purchase | ExamAccessPurchase | None

    @property
    def ok(self):
        return self.status in (FULFILLED, ALREADY_FULFILLED)

    @property
    def includes_exam(self):
        return self.kind == 'upgrade' or (self.kind == 'purchase' and self.record.package == PACKAGE_BOOK_EXAM)

    def __repr__(self):
        return f'<FulfilResult {self.status} {self.kind}>'


def _find_record(reference):
    p = Purchase.query.filter_by(payment_reference=reference).first()
    if p:
        return 'purchase', p
    u = ExamAccessPurchase.query.filter_by(payment_reference=reference).first()
    if u:
        return 'upgrade', u
    return None, None


def fulfil_charge(data: dict, ref_code=None) -> FulfilResult:
    """Apply a Paystack transaction (the `data` object from verify or from a
    charge.success event). Verifies status and paid amount (kobo) against the
    server-computed amount stored on the record, flips it to success at most
    once, commits, then (only on the first flip) pushes the exam grant."""
    reference = (data or {}).get('reference')
    if not reference:
        return FulfilResult(NOT_FOUND)
    kind, record = _find_record(reference)
    if record is None:
        logger.warning('Paystack charge for unknown reference %s', reference)
        return FulfilResult(NOT_FOUND)
    if record.payment_status == 'success':
        return FulfilResult(ALREADY_FULFILLED, kind, record)
    if data.get('status') != 'success':
        return FulfilResult(NOT_SUCCESS, kind, record)

    expected_kobo = naira_to_kobo(record.amount_paid)
    try:
        paid_kobo = int(data.get('amount') or 0)
    except (TypeError, ValueError):
        paid_kobo = 0
    currency = data.get('currency')
    if paid_kobo < expected_kobo or (currency and currency != 'NGN'):
        logger.error('Rejected underpaid charge %s: paid %s %s, expected %s kobo',
                     reference, paid_kobo, currency, expected_kobo)
        return FulfilResult(AMOUNT_TOO_LOW, kind, record)

    model = Purchase if kind == 'purchase' else ExamAccessPurchase
    # Atomic guard: only one concurrent caller can flip pending -> success.
    flipped = model.query.filter(
        model.id == record.id, model.payment_status != 'success'
    ).update({'payment_status': 'success'}, synchronize_session=False)
    if flipped != 1:
        db.session.rollback()
        db.session.refresh(record)
        return FulfilResult(ALREADY_FULFILLED, kind, record)

    if kind == 'purchase':
        if not LibraryItem.query.filter_by(user_id=record.user_id, book_id=record.book_id).first():
            db.session.add(LibraryItem(user_id=record.user_id, book_id=record.book_id))
        attribute_referral(record, ref_code)
    db.session.commit()
    db.session.refresh(record)

    result = FulfilResult(FULFILLED, kind, record)
    if result.includes_exam:
        send_exam_grant(kind, record)
    return result


def _event_id(kind, record):
    return f"{'purchase' if kind == 'purchase' else 'upgrade'}:{record.payment_reference}"


def send_exam_grant(kind, record, timeout=itest_client.DEFAULT_TIMEOUT) -> bool:
    """Push one grant to iTest and record the outcome on the row. Never
    raises - a failure is stored in exam_access_last_error for retry."""
    if record.exam_access_granted_at is not None:
        return True
    if not itest_client.is_configured():
        logger.warning('iTest not configured - exam grant for %s left pending', record.payment_reference)
        record.exam_access_last_error = 'iTest not configured (ITEST_BASE_URL / ITEST_WEBHOOK_SECRET)'
        db.session.commit()
        return False

    user = db.session.get(User, record.user_id)
    book = db.session.get(Book, record.book_id)
    try:
        itest_client.grant_exam_access(
            event_id=_event_id(kind, record),
            email=user.email,
            full_name=user.full_name,
            exam_keys=book.exam_keys or [],
            reference=record.payment_reference,
            book_id=book.id,
            book_title=book.title,
            timeout=timeout,
        )
    except Exception as exc:  # ITestError or anything unexpected - don't break payments
        record.exam_access_last_error = f'{datetime.utcnow().isoformat()}Z {exc}'[:2000]
        db.session.commit()
        return False

    record.exam_access_granted_at = datetime.utcnow()
    record.exam_access_last_error = None
    db.session.commit()
    return True


def pending_exam_grants(user_id=None, limit=None):
    """Successful exam purchases/upgrades iTest hasn't confirmed yet."""
    q1 = Purchase.query.filter(Purchase.payment_status == 'success',
                               Purchase.package == PACKAGE_BOOK_EXAM,
                               Purchase.exam_access_granted_at.is_(None))
    q2 = ExamAccessPurchase.query.filter(ExamAccessPurchase.payment_status == 'success',
                                         ExamAccessPurchase.exam_access_granted_at.is_(None))
    if user_id is not None:
        q1 = q1.filter(Purchase.user_id == user_id)
        q2 = q2.filter(ExamAccessPurchase.user_id == user_id)
    q1 = q1.order_by(Purchase.id)
    q2 = q2.order_by(ExamAccessPurchase.id)
    if limit is not None:
        q1 = q1.limit(limit)
        q2 = q2.limit(limit)
    items = [('purchase', p) for p in q1.all()] + [('upgrade', u) for u in q2.all()]
    return items[:limit] if limit is not None else items


def retry_pending_exam_grants(user_id=None, limit=None, timeout=itest_client.DEFAULT_TIMEOUT):
    """Resend every pending grant (optionally only one user's, at most
    `limit`). Returns {'attempted', 'granted', 'failed'}. No-op when iTest
    isn't configured."""
    stats = {'attempted': 0, 'granted': 0, 'failed': 0}
    if not itest_client.is_configured():
        return stats
    for kind, record in pending_exam_grants(user_id=user_id, limit=limit):
        stats['attempted'] += 1
        if send_exam_grant(kind, record, timeout=timeout):
            stats['granted'] += 1
        else:
            stats['failed'] += 1
    return stats
