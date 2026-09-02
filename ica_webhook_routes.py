"""
Single inbound endpoint for every Paystack event this app cares about,
relayed by ICA's centralized webhook relay (see Iglobals-CAuth's
docs/PAYSTACK_WEBHOOK_RELAY.md) rather than received directly from Paystack.

Why one endpoint for two different flows (book purchases, subscriptions):
ICA's client_webhook_configs table stores exactly ONE webhook_url per
(client_id, provider) - it can't fan out to two different URLs for the same
app. So both flows' Paystack calls now tag their `metadata` with a `purpose`
field ('book_purchase' | 'subscription'), and this route dispatches on that
instead of running two separate webhook receivers.

Signature: verifies x-ica-relay-signature using ICA_WEBHOOK_RELAY_SECRET -
the per-client secret ICA generated when this app's webhook was registered
in the admin panel (Settings > Clients > this app > Payment webhooks). This
is NOT Paystack's own secret - never verify this against PAYSTACK_SECRET_KEY.
"""
import hashlib
import hmac
import logging

from flask import current_app, jsonify, request

from app import app
import routes as book_routes
import subscription_routes

logger = logging.getLogger(__name__)


@app.route('/api/webhooks/ica-relay/paystack', methods=['POST'])
def ica_relay_paystack():
    relay_secret = current_app.config.get('ICA_WEBHOOK_RELAY_SECRET', '').encode()
    signature = request.headers.get('x-ica-relay-signature', '')
    computed = hmac.new(relay_secret, request.get_data(), hashlib.sha512).hexdigest()

    if not hmac.compare_digest(computed, signature):
        logger.warning("Rejected ICA relay call with invalid signature.")
        return jsonify({"error": "invalid signature"}), 401

    payload = request.get_json(silent=True) or {}
    event = payload.get("event")
    data = payload.get("data", {})
    purpose = (data.get("metadata") or {}).get("purpose")

    if purpose == 'book_purchase':
        if event == 'charge.success':
            book_routes.handle_book_charge_success(data)
    elif purpose == 'subscription':
        if event == 'charge.success':
            subscription_routes._apply_successful_charge(data)
        elif event == 'subscription.create':
            subscription_routes._attach_subscription_credentials(data)
        elif event in ('subscription.disable', 'subscription.not_renew'):
            subscription_routes._mark_cancelled(data)
    else:
        logger.warning("ICA relay event with unknown/missing purpose=%r, event=%s", purpose, event)

    return jsonify({"received": True}), 200
