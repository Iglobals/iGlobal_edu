import random
import string
import os
import secrets
from functools import wraps
from flask import (render_template, request, redirect, url_for,
                   flash, session, make_response, jsonify)
from werkzeug.security import generate_password_hash, check_password_hash
from app import app
from extensions import db
from models import ReferralAgent, ReferralCommission, Book, Purchase, REFERRAL_COOKIE_DAYS

AGENT_SESSION_KEY = 'agent_id'


# ── Helpers ───────────────────────────────────────────────────────────────

def generate_ref_code():
    chars = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choices(chars, k=7))
        if not ReferralAgent.query.filter_by(ref_code=code).first():
            return code


def agent_login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if AGENT_SESSION_KEY not in session:
            return redirect(url_for('agent_login'))
        return f(*args, **kwargs)
    return decorated


def current_agent():
    aid = session.get(AGENT_SESSION_KEY)
    return ReferralAgent.query.get(aid) if aid else None


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


# ── Agent auth ────────────────────────────────────────────────────────────

@app.route('/agents/register', methods=['GET', 'POST'])
def agent_register():
    if request.method == 'POST':
        username   = request.form.get('username', '').strip()
        first_name = request.form.get('first_name', '').strip()
        email      = request.form.get('email', '').strip().lower()
        password   = request.form.get('password', '')
        confirm    = request.form.get('confirm_password', '')

        if not all([username, first_name, email, password]):
            flash('All fields are required.', 'danger')
        elif ReferralAgent.query.filter_by(email=email).first():
            flash('An agent account with that email already exists.', 'danger')
        elif ReferralAgent.query.filter_by(username=username).first():
            flash('That username is taken.', 'danger')
        elif len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
        elif password != confirm:
            flash('Passwords do not match.', 'danger')
        else:
            agent = ReferralAgent(
                username=username,
                first_name=first_name,
                email=email,
                password_hash=generate_password_hash(password),
                ref_code=generate_ref_code()
            )
            db.session.add(agent)
            db.session.commit()
            session[AGENT_SESSION_KEY] = agent.id
            return redirect(url_for('agent_dashboard'))

    return render_template('referral/register.html', google_enabled=_GOOGLE_ENABLED)


@app.route('/agents/login', methods=['GET', 'POST'])
def agent_login():
    if AGENT_SESSION_KEY in session:
        return redirect(url_for('agent_dashboard'))

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        agent    = ReferralAgent.query.filter_by(email=email).first()

        if not agent:
            flash('No agent account found with that email.', 'danger')
        elif not check_password_hash(agent.password_hash, password):
            flash('Incorrect password.', 'danger')
        elif not agent.is_active:
            flash('Your account has been deactivated. Contact support.', 'danger')
        else:
            session[AGENT_SESSION_KEY] = agent.id
            return redirect(url_for('agent_dashboard'))

    return render_template('referral/login.html', google_enabled=_GOOGLE_ENABLED)


@app.route('/agents/logout')
def agent_logout():
    session.pop(AGENT_SESSION_KEY, None)
    return redirect(url_for('agent_login'))


# ── Agent dashboard ───────────────────────────────────────────────────────

@app.route('/agents/dashboard')
@agent_login_required
def agent_dashboard():
    agent = current_agent()
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
    from flask_login import current_user
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
    from flask_login import current_user
    if not current_user.is_authenticated or not current_user.is_admin:
        return jsonify({'error': 'forbidden'}), 403

    commission = ReferralCommission.query.get_or_404(commission_id)
    commission.is_paid = True
    db.session.commit()
    return jsonify({'status': 'ok'})


@app.route('/admin/referrals/agent/<int:agent_id>/mark-all-paid', methods=['POST'])
def admin_mark_all_paid(agent_id):
    from flask_login import current_user
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


# ── Google OAuth for agents ───────────────────────────────────────────────

_GOOGLE_ENABLED = bool(
    os.environ.get('GOOGLE_CLIENT_ID', '') and
    os.environ.get('GOOGLE_CLIENT_ID', '') != 'your-google-client-id-here'
)


@app.route('/agents/auth/google')
def agent_google_login():
    if not _GOOGLE_ENABLED:
        flash('Google sign-in is temporarily unavailable. Please use email and password.', 'warning')
        return redirect(url_for('agent_login'))
    from routes import google
    redirect_uri = url_for('agent_google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route('/agents/auth/google/callback')
def agent_google_callback():
    if not _GOOGLE_ENABLED:
        return redirect(url_for('agent_login'))
    try:
        from routes import google
        token = google.authorize_access_token()
        user_info = token.get('userinfo')
        if not user_info:
            flash('Google authentication failed.', 'danger')
            return redirect(url_for('agent_login'))

        email = user_info.get('email')
        name  = user_info.get('given_name') or user_info.get('name', email.split('@')[0])
        username = email.split('@')[0]

        agent = ReferralAgent.query.filter_by(email=email).first()
        if not agent:
            # Auto-generate unique username
            base = username
            i = 1
            while ReferralAgent.query.filter_by(username=username).first():
                username = f'{base}{i}'; i += 1
            agent = ReferralAgent(
                username=username,
                first_name=name,
                email=email,
                password_hash=generate_password_hash(secrets.token_hex(16)),
                ref_code=generate_ref_code()
            )
            db.session.add(agent)
            db.session.commit()

        session[AGENT_SESSION_KEY] = agent.id
        return redirect(url_for('agent_dashboard'))
    except Exception:
        flash('Google sign-in failed. Please try again or use email and password.', 'danger')
        return redirect(url_for('agent_login'))
