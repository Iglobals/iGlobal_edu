"""
iGlobals Central Auth (ICA) integration.

Replaces native email/password signup, login, and password reset. Every
account — including referral agents — is identified by its ICA `sub` claim.
Mirrors the pattern used in iTest's app/auth/routes.py, adapted to this
app's Flask-Login-based session handling instead of a raw session cookie.
"""
import os
import uuid
from datetime import datetime, timedelta

from flask import redirect, url_for, request, session, flash
from flask_login import login_user, logout_user, current_user
from iglobals_auth import IGlobalsAuth

from app import app
from extensions import db
from models import User, ApprovedAgent, ReferralAgent

# ── PKCE state store ────────────────────────────────────────────────────────
# Not the Flask session — separate function invocations (e.g. on Vercel) don't
# reliably share cookies/state across the redirect to ICA and back. Keyed by
# the `state` value instead, in Redis if configured, else in-process memory.

_redis_client = None
_memory_store = {}


def get_redis():
    global _redis_client
    if _redis_client is None:
        redis_url = os.environ.get('REDIS_URL')
        if redis_url:
            try:
                import redis
                _redis_client = redis.from_url(redis_url, decode_responses=True)
                _redis_client.ping()
            except Exception:
                _redis_client = False
        else:
            _redis_client = False
    return _redis_client if _redis_client else None


def store_oauth_state(state, code_verifier, next_url=None):
    payload = f"{code_verifier}|{next_url or ''}"
    redis_client = get_redis()
    if redis_client:
        redis_client.setex(f"oauth_state:{state}", timedelta(minutes=10), payload)
    else:
        _memory_store[state] = {'payload': payload, 'expires_at': datetime.utcnow() + timedelta(minutes=10)}


def get_oauth_state(state):
    redis_client = get_redis()
    if redis_client:
        payload = redis_client.get(f"oauth_state:{state}")
    else:
        data = _memory_store.get(state)
        payload = data['payload'] if data and data['expires_at'] > datetime.utcnow() else None

    if not payload:
        return None
    code_verifier, _, next_url = payload.partition('|')
    return {'code_verifier': code_verifier, 'next_url': next_url or None}


def delete_oauth_state(state):
    redis_client = get_redis()
    if redis_client:
        redis_client.delete(f"oauth_state:{state}")
    else:
        _memory_store.pop(state, None)


def get_ica_client():
    return IGlobalsAuth(
        base_url=app.config['ICA_BASE_URL'],
        client_id=app.config['ICA_CLIENT_ID'],
        client_secret=app.config['ICA_CLIENT_SECRET'],
        redirect_uri=app.config['ICA_REDIRECT_URI'],
        scopes=['openid', 'profile', 'email']
    )


# ── Identity resolution ─────────────────────────────────────────────────────

class UnverifiedEmailConflict(Exception):
    """Raised when ICA reports an unverified email that already belongs to an existing account."""
    pass


def get_or_create_user(user_info):
    """
    Find the local User for this ICA identity, linking or creating as needed:
      1. Already linked (ica_sub matches) — the common case on every later login.
      2. A legacy account with the same email exists but has never logged in via
         ICA yet — link it in place so their purchases/library/reviews carry over.
      3. Neither — brand new account.
    """
    sub = user_info.get('sub')
    email = user_info.get('email')
    email_verified = bool(user_info.get('email_verified'))
    full_name = f"{user_info.get('given_name', '')} {user_info.get('family_name', '')}".strip() or (email or 'User')

    user = User.query.filter_by(ica_sub=sub).first()
    if user:
        return user

    # Only link to a pre-existing account by email if ICA has actually verified
    # the caller controls that inbox — otherwise anyone claiming someone else's
    # email at signup could walk straight into their existing purchases/library.
    if email:
        existing = User.query.filter_by(email=email).first()
        if existing:
            if not email_verified:
                raise UnverifiedEmailConflict(email)
            existing.ica_sub = sub
            db.session.commit()
            return existing

    user = User(ica_sub=sub, full_name=full_name, email=email)
    db.session.add(user)
    db.session.commit()
    return user


def sync_agent_profile(user):
    """
    If this user's email is on the agent allowlist, make sure they have a
    ReferralAgent profile — being an agent is a role on top of the normal ICA
    identity, not a separate account. Safe to call on every login.
    """
    if ReferralAgent.query.filter_by(user_id=user.id).first():
        return
    if not ApprovedAgent.query.filter_by(email=user.email).first():
        return

    # A pre-migration agent row for this email (created back when agents had
    # their own password login) — link it instead of creating a duplicate, so
    # their existing ref_code and commission history carry over.
    existing = ReferralAgent.query.filter_by(email=user.email).first()
    if existing:
        existing.user_id = user.id
        db.session.commit()
        return

    from referral_routes import generate_ref_code
    agent = ReferralAgent(
        user_id=user.id,
        first_name=user.full_name.split()[0] if user.full_name else 'Agent',
        email=user.email,
        ref_code=generate_ref_code()
    )
    db.session.add(agent)
    db.session.commit()


# ── Routes ───────────────────────────────────────────────────────────────────

@app.route('/auth/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('library'))

    client = get_ica_client()
    pkce = client.generate_pkce()
    state = str(uuid.uuid4())

    store_oauth_state(state, pkce['code_verifier'], next_url=request.args.get('next'))

    return redirect(client.get_authorization_url(state, pkce['code_challenge']))


@app.route('/auth/callback')
def callback():
    state = request.args.get('state')
    state_data = get_oauth_state(state)
    if not state_data:
        flash('Your login attempt expired. Please try again.', 'danger')
        return redirect(url_for('login'))

    code = request.args.get('code')
    if not code:
        flash('Login was cancelled or failed. Please try again.', 'danger')
        return redirect(url_for('login'))

    try:
        client = get_ica_client()
        tokens = client.exchange_code(code, state_data['code_verifier'])
        delete_oauth_state(state)

        user_info = client.get_user_info(tokens.access_token)
        user = get_or_create_user(user_info)
        sync_agent_profile(user)

        login_user(user, remember=True)
        session.permanent = True

        return redirect(state_data['next_url'] or url_for('library'))
    except UnverifiedEmailConflict:
        flash('An account with this email already exists. Please verify this email address with iGlobals Central Auth before signing in, so we can safely match it to your existing account.', 'danger')
        return redirect(url_for('login'))
    except Exception:
        flash('Sign-in failed. Please try again.', 'danger')
        return redirect(url_for('login'))


@app.route('/logout')
def logout():
    # logout_user() already pops the session's login keys AND - critically -
    # notices the remember_token cookie on this request and marks it for
    # deletion (session['_remember'] = 'clear', consumed by Flask-Login's own
    # after_request hook). A follow-up session.clear() used to wipe that flag
    # out before Flask-Login could read it, so the remember cookie survived
    # logout and silently logged the user back in on their very next request.
    logout_user()
    return redirect(url_for('index'))
