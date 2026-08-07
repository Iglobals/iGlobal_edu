import random
import string
import os
from functools import wraps
from flask import (render_template, request, redirect, url_for,
                   flash, make_response, jsonify)
from flask_login import current_user
from app import app
from extensions import db
from models import ReferralAgent, ReferralCommission, Book, Purchase, REFERRAL_COOKIE_DAYS, ApprovedAgent


# ── Helpers ───────────────────────────────────────────────────────────────
# Being an agent is a role on top of the normal ICA-authenticated identity,
# not a separate login. See auth_routes.sync_agent_profile — an approved
# email gets its ReferralAgent profile created automatically on ICA login.

def generate_ref_code():
    chars = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choices(chars, k=7))
        if not ReferralAgent.query.filter_by(ref_code=code).first():
            return code


def current_agent():
    if not current_user.is_authenticated:
        return None
    return ReferralAgent.query.filter_by(user_id=current_user.id).first()


def agent_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login', next=request.path))
        if not current_agent():
            flash('Your email is not authorized as an agent. Please contact iglobalsedu@gmail.com to get access.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated


# ── Cookie tracking ───────────────────────────────────────────────────────

@app.route('/ref/<ref_code>')
def referral_redirect(ref_code):
    """
    Short link: /ref/a2b45ef  →  redirects to the book payment page
    with the ref cookie set.
    book_id is passed as ?b=3
    """
    book_id = request.args.get('b', type=int)
    agent = ReferralAgent.query.filter_by(ref_code=ref_code, is_active=True).first()

    if not agent or not book_id:
        return redirect(url_for('index'))

    target = url_for('payment', book_id=book_id, ref=ref_code)
    resp = make_response(redirect(target))
    resp.set_cookie(
        'igref', ref_code,
        max_age=REFERRAL_COOKIE_DAYS * 86400,
        httponly=True, samesite='Lax'
    )
    return resp


# ── Agent dashboard ───────────────────────────────────────────────────────

@app.route('/agents/dashboard')
@agent_required
def agent_dashboard():
    agent = current_agent()
    if not agent.is_active:
        flash('Your agent account has been deactivated. Contact support.', 'danger')
        return redirect(url_for('index'))
    commissions = ReferralCommission.query.filter_by(agent_id=agent.id).order_by(
        ReferralCommission.created_at.desc()).all()

    total_earned   = sum(c.amount_earned for c in commissions)
    total_paid     = sum(c.amount_earned for c in commissions if c.is_paid)
    total_unpaid   = total_earned - total_paid
    total_sales    = len(commissions)

    # Build referral link base from env, fallback to request host
    base_url = os.environ.get('APP_BASE_URL', request.host_url.rstrip('/'))

    return render_template('referral/dashboard.html',
                           agent=agent,
                           commissions=commissions,
                           total_earned=total_earned,
                           total_paid=total_paid,
                           total_unpaid=total_unpaid,
                           total_sales=total_sales,
                           base_url=base_url)


# ── Admin: referrals overview ─────────────────────────────────────────────

@app.route('/admin/referrals')
def admin_referrals():
    if not current_user.is_authenticated or not current_user.is_admin:
        return redirect(url_for('index'))

    agents = ReferralAgent.query.order_by(ReferralAgent.created_at.desc()).all()
    data = []
    for a in agents:
        comms = a.commissions
        earned = sum(c.amount_earned for c in comms)
        paid   = sum(c.amount_earned for c in comms if c.is_paid)
        if earned > 0:   # only show agents with at least one sale
            data.append({
                'agent':   a,
                'sales':   len(comms),
                'earned':  earned,
                'paid':    paid,
                'unpaid':  earned - paid,
            })

    return render_template('referral/admin_referrals.html', data=data)


@app.route('/admin/referrals/<int:commission_id>/mark-paid', methods=['POST'])
def admin_mark_paid(commission_id):
    if not current_user.is_authenticated or not current_user.is_admin:
        return jsonify({'error': 'forbidden'}), 403

    commission = ReferralCommission.query.get_or_404(commission_id)
    commission.is_paid = True
    db.session.commit()
    return jsonify({'status': 'ok'})


@app.route('/admin/referrals/agent/<int:agent_id>/mark-all-paid', methods=['POST'])
def admin_mark_all_paid(agent_id):
    if not current_user.is_authenticated or not current_user.is_admin:
        return jsonify({'error': 'forbidden'}), 403

    ReferralCommission.query.filter_by(agent_id=agent_id, is_paid=False).update({'is_paid': True})
    db.session.commit()
    return jsonify({'status': 'ok'})


# ── Books list API (for agent link generator) ─────────────────────────────

@app.route('/api/agent/books')
def agent_books_list():
    """Returns all non-free books grouped by category for the agent dashboard."""
    books = Book.query.filter_by(is_free=False).order_by(Book.category, Book.title).all()
    result = {}
    for b in books:
        result.setdefault(b.category, []).append({
            'id': b.id,
            'title': b.title,
            'price': b.price_naira
        })
    return jsonify(result)
