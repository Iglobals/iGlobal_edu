"""
Pro subscription: recurring Paystack billing, unlocking StudyNeat AI +
iTest exam access for the user's ENTIRE library (not scoped to one book).
Requires owning at least one book first - there is no standalone "just
subscribe" path, since Pro has no value without a book to apply it to.

Uses the SAME Paystack inline-popup pattern already established in this
codebase (see templates/payment.html / routes.py's initialize_payment) -
PaystackPop.setup() client-side with a `plan` code, rather than the
server-redirect-to-hosted-checkout style - so this app has one consistent
Paystack integration idiom, not two. verify-then-apply is still idempotent
via provider_ref, and the webhook is still the authoritative backstop in
case the browser never returns from the popup (tab closed, network drop).
"""
import hashlib
import hmac
import logging
from datetime import datetime, timedelta

from flask import current_app, flash, jsonify, redirect, render_template, request, url_for
from flask_login import current_user, login_required

import paystack_client
from app import app, db
from models import Purchase, Subscription, SubscriptionPayment, SubscriptionPlan, User
from paystack_client import PaystackError

logger = logging.getLogger(__name__)

INTERVAL_TO_DAYS = {"monthly": 30, "annual": 365}


@app.route('/subscribe')
@login_required
def subscribe():
    owns_a_book = Purchase.query.filter_by(user_id=current_user.id, payment_status='success').first() is not None
    if not owns_a_book:
        flash('Buy at least one book before subscribing to Pro - the plan applies to books you own.', 'warning')
        return redirect(url_for('library'))

    plans = {p.interval: p for p in SubscriptionPlan.query.filter_by(is_active=True).all()}
    return render_template(
        'subscribe.html', plans=plans,
        paystack_public_key=current_app.config['PAYSTACK_PUBLIC_KEY'],
        ica_client_id=current_app.config.get('ICA_CLIENT_ID', ''),
    )


@app.route('/subscribe/verify/<reference>')
@login_required
def subscribe_verify(reference):
    try:
        data = paystack_client.verify_transaction(reference)
    except PaystackError as exc:
        logger.error("Paystack verify failed for reference=%s: %s", reference, exc)
        flash("Couldn't confirm your payment - if you were charged, it'll be applied shortly via webhook.", 'error')
        return redirect(url_for('subscribe'))

    if data.get("status") == "success":
        _apply_successful_charge(data)
        flash("You're on Pro - AI features and exams are unlocked for your library.", 'success')
        return redirect(url_for('manage_subscription'))

    flash("Payment was not successful.", 'error')
    return redirect(url_for('subscribe'))


@app.route('/subscribe/webhook', methods=['POST'])
def subscribe_webhook():
    """No @login_required - Paystack calls this directly. Trust comes from
    the signature, not a session, same pattern as the existing
    paystack_webhook() in routes.py for one-off book purchases."""
    secret_key = current_app.config.get('PAYSTACK_SECRET_KEY', '').encode()
    signature = request.headers.get('x-paystack-signature', '')
    computed = hmac.new(secret_key, request.get_data(), hashlib.sha512).hexdigest()

    if not hmac.compare_digest(computed, signature):
        logger.warning("Rejected subscribe webhook call with invalid Paystack signature.")
        return jsonify({"error": "invalid signature"}), 401

    payload = request.get_json(silent=True) or {}
    event = payload.get("event")
    data = payload.get("data", {})

    if event == "charge.success":
        _apply_successful_charge(data)
    elif event == "subscription.create":
        _attach_subscription_credentials(data)
    elif event in ("subscription.disable", "subscription.not_renew"):
        _mark_cancelled(data)
    else:
        logger.info("Unhandled Paystack subscribe webhook event: %s", event)

    return jsonify({"received": True}), 200


@app.route('/subscribe/manage')
@login_required
def manage_subscription():
    sub = Subscription.query.filter_by(user_id=current_user.id).first()
    last_payment = (
        SubscriptionPayment.query.filter_by(user_id=current_user.id).order_by(SubscriptionPayment.paid_at.desc()).first()
    )
    return render_template('manage_subscription.html', sub=sub, last_payment=last_payment)


@app.route('/subscribe/cancel', methods=['POST'])
@login_required
def cancel_subscription():
    sub = Subscription.query.filter_by(user_id=current_user.id).first()
    if not sub or not sub.paystack_subscription_code or not sub.paystack_email_token:
        flash("No active subscription to cancel.", 'error')
        return redirect(url_for('manage_subscription'))

    try:
        paystack_client.disable_subscription(sub.paystack_subscription_code, sub.paystack_email_token)
    except PaystackError as exc:
        logger.error("Paystack disable_subscription failed for user=%s: %s", current_user.id, exc)
        flash("Couldn't cancel right now - please try again shortly.", 'error')
        return redirect(url_for('manage_subscription'))

    sub.status = 'cancelled'
    db.session.commit()
    flash("Subscription cancelled - you'll keep Pro access until the current period ends.", 'success')
    return redirect(url_for('manage_subscription'))


def _apply_successful_charge(data: dict):
    reference = data.get("reference")
    if not reference or SubscriptionPayment.query.filter_by(provider_ref=reference).first():
        return  # already processed - callback and webhook can both land for the same charge

    metadata = data.get("metadata") or {}
    user_id = metadata.get("user_id")
    interval = metadata.get("interval")
    user = User.query.get(user_id) if user_id else User.query.filter_by(email=(data.get("customer") or {}).get("email")).first()
    if not user or not interval:
        logger.error("Paystack subscribe charge.success for reference=%s matched no user/interval.", reference)
        return

    plan_row = SubscriptionPlan.query.filter_by(interval=interval).first()

    sub = Subscription.query.filter_by(user_id=user.id).first()
    if sub is None:
        sub = Subscription(user_id=user.id)
    sub.plan_id = plan_row.id if plan_row else sub.plan_id
    sub.status = 'active'
    sub.current_period_end = datetime.utcnow() + timedelta(days=INTERVAL_TO_DAYS.get(interval, 30))
    sub.paystack_customer_code = (data.get("customer") or {}).get("customer_code")
    db.session.add(sub)

    db.session.add(SubscriptionPayment(
        user_id=user.id,
        plan_id=plan_row.id if plan_row else None,
        provider_ref=reference,
        amount_ngn=data.get("amount", 0) / 100,
        status="success",
        paid_at=datetime.utcnow(),
    ))
    db.session.commit()


def _attach_subscription_credentials(data: dict):
    """subscription.create is the only event carrying email_token, required
    (with subscription_code) by Paystack's Disable Subscription API."""
    email = (data.get("customer") or {}).get("email")
    user = User.query.filter_by(email=email).first() if email else None
    sub = Subscription.query.filter_by(user_id=user.id).first() if user else None
    if not sub:
        logger.error("Paystack subscription.create matched no subscription (email=%s).", email)
        return
    sub.paystack_subscription_code = data.get("subscription_code")
    sub.paystack_email_token = data.get("email_token")
    db.session.commit()


def _mark_cancelled(data: dict):
    email = (data.get("customer") or {}).get("email")
    user = User.query.filter_by(email=email).first() if email else None
    sub = Subscription.query.filter_by(user_id=user.id).first() if user else None
    if sub:
        sub.status = 'cancelled'
        db.session.commit()
