"""
iGlobals Educational Services - Database Models
"""

from extensions import db
from flask_login import UserMixin
from datetime import datetime


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    ica_sub = db.Column(db.String(255), unique=True, nullable=True)   # iGlobals Central Auth subject id
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    reviews = db.relationship('Review', backref='user', lazy=True, cascade='all, delete-orphan')
    favorites = db.relationship('Favorite', backref='user', lazy=True, cascade='all, delete-orphan')
    purchases = db.relationship('Purchase', backref='user', lazy=True, cascade='all, delete-orphan')
    notes = db.relationship('Note', backref='user', lazy=True, cascade='all, delete-orphan')
    library_items = db.relationship('LibraryItem', backref='user', lazy=True, cascade='all, delete-orphan')
    agent_profile = db.relationship('ReferralAgent', backref='user', lazy=True, uselist=False)


class Book(db.Model):
    __tablename__ = 'books'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(500))
    price_naira = db.Column(db.Float, default=0.0)
    is_free = db.Column(db.Boolean, default=False)
    chapters = db.Column(db.JSON)  # chapter TITLES only - content lives in Mongo, see mongo_books.py
    # JUPEB exam-access package (see exam_packages.py). exam_keys are iTest
    # exam keys; a null/0 add-on price means no exam package is offered.
    # Package price = price_naira + exam_addon_price_naira.
    exam_keys = db.Column(db.JSON, default=list)
    exam_addon_price_naira = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    reviews = db.relationship('Review', backref='book', lazy=True, cascade='all, delete-orphan')
    favorites = db.relationship('Favorite', backref='book', lazy=True, cascade='all, delete-orphan')
    purchases = db.relationship('Purchase', backref='book', lazy=True, cascade='all, delete-orphan')
    notes = db.relationship('Note', backref='book', lazy=True, cascade='all, delete-orphan')
    library_items = db.relationship('LibraryItem', backref='book', lazy=True, cascade='all, delete-orphan')


class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id', ondelete='CASCADE'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    likes = db.Column(db.Integer, default=0)
    dislikes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Favorite(db.Model):
    __tablename__ = 'favorites'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'book_id', name='unique_favorite'),)


class Purchase(db.Model):
    __tablename__ = 'purchases'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id', ondelete='CASCADE'), nullable=False)
    amount_paid = db.Column(db.Float, nullable=False)
    payment_reference = db.Column(db.String(100), unique=True)
    payment_status = db.Column(db.String(20), default='pending')
    # 'book' | 'book_exam' - amount_paid is the server-computed price of this
    # package. Exam access bought later goes in ExamAccessPurchase instead.
    package = db.Column(db.String(20), nullable=False, default='book', server_default='book')
    exam_access_granted_at = db.Column(db.DateTime, nullable=True)   # iTest confirmed the grant
    exam_access_last_error = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'book_id', name='unique_purchase'),)


class ExamAccessPurchase(db.Model):
    """An exam-access UPGRADE for a book the user already owns as 'book' only.
    Separate table because purchases has unique (user_id, book_id) and the
    upgrade needs its own Paystack reference / amount / status. One row per
    (user, book), reused while pending - same pattern as Purchase."""
    __tablename__ = 'exam_access_purchases'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id', ondelete='CASCADE'), nullable=False)
    amount_paid = db.Column(db.Float, nullable=False)
    payment_reference = db.Column(db.String(100), unique=True)
    payment_status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    exam_access_granted_at = db.Column(db.DateTime, nullable=True)
    exam_access_last_error = db.Column(db.Text, nullable=True)

    user = db.relationship('User', backref=db.backref('exam_access_purchases', lazy=True, cascade='all, delete-orphan'))
    book = db.relationship('Book', backref=db.backref('exam_access_purchases', lazy=True, cascade='all, delete-orphan'))

    __table_args__ = (db.UniqueConstraint('user_id', 'book_id', name='unique_exam_access_purchase'),)


def get_exam_access(user_id, book_id):
    """(source, record) for the user's exam access to this book, where source
    is 'purchase' (bought as book_exam) or 'upgrade', or (None, None).
    Only successful payments count; record.exam_access_granted_at says
    whether iTest has confirmed it yet."""
    p = Purchase.query.filter_by(user_id=user_id, book_id=book_id,
                                 payment_status='success', package='book_exam').first()
    if p:
        return 'purchase', p
    u = ExamAccessPurchase.query.filter_by(user_id=user_id, book_id=book_id,
                                           payment_status='success').first()
    if u:
        return 'upgrade', u
    return None, None


class LibraryItem(db.Model):
    __tablename__ = 'library_items'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'book_id', name='unique_library_item'),)


class SubscriptionPlan(db.Model):
    """A purchasable Pro plan tier (monthly/annual). Price lives here, not in
    code, so it can be changed without a deploy - see seed_subscription_plans.py."""
    __tablename__ = 'subscription_plans'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    interval = db.Column(db.String(20), nullable=False)  # 'monthly' | 'annual'
    price_ngn = db.Column(db.Float, nullable=False)
    price_usd = db.Column(db.Float)
    paystack_plan_code = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    subscriptions = db.relationship('Subscription', backref='plan', lazy=True)


class Subscription(db.Model):
    """A user's Pro subscription - unlocks StudyNeat AI + iTest exam access
    for their ENTIRE library (present and future book purchases), not scoped
    to one book. Requires the user to already own at least one book before
    they can subscribe (enforced in subscription_routes.py, not here)."""
    __tablename__ = 'subscriptions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plans.id'), nullable=False)
    status = db.Column(db.String(20), default='active')  # active | cancelled | expired
    paystack_customer_code = db.Column(db.String(100))
    paystack_subscription_code = db.Column(db.String(100))
    paystack_email_token = db.Column(db.String(255))  # required (with subscription_code) by Paystack's Disable Subscription API
    current_period_end = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def is_active(self) -> bool:
        """True only while status is active AND the paid period hasn't lapsed -
        a cancelled subscription keeps access until current_period_end, same
        as iTest's billing model."""
        if self.status not in ('active', 'cancelled'):
            return False
        if self.current_period_end is None:
            return False
        return self.current_period_end > datetime.utcnow()


def get_active_subscription(user_id):
    """Single source of truth for 'does this user have Pro' - used by the
    subscribe gate, the StudyNeat launch route, and reading.html's template
    context alike, so the eligibility rule never drifts between call sites."""
    sub = Subscription.query.filter_by(user_id=user_id).first()
    if sub and sub.is_active():
        return sub
    return None


class SubscriptionPayment(db.Model):
    """Payment ledger for subscriptions - separate from Purchase, which is
    one-off book buys. Mirrors iTest's Payment model/pattern."""
    __tablename__ = 'subscription_payments'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plans.id'))
    provider = db.Column(db.String(20), default='paystack')
    provider_ref = db.Column(db.String(100), unique=True, nullable=False)
    amount_ngn = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='success')
    paid_at = db.Column(db.DateTime, default=datetime.utcnow)


class Note(db.Model):
    __tablename__ = 'notes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id', ondelete='CASCADE'), nullable=False)
    chapter_number = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ── Referral System ───────────────────────────────────────────────────────

REFERRAL_COMMISSION_RATE = 0.30   # 30% — change here to update globally
REFERRAL_COOKIE_DAYS     = 5

class ApprovedAgent(db.Model):
    __tablename__ = 'approved_agents'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class ReferralAgent(db.Model):
    __tablename__ = 'referral_agents'

    id            = db.Column(db.Integer, primary_key=True)
    # Nullable: pre-existing agent rows are only linked to their ICA identity
    # the next time that agent logs in (see auth_routes.sync_agent_profile).
    user_id       = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=True)
    first_name    = db.Column(db.String(80), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    ref_code      = db.Column(db.String(7), unique=True, nullable=False)
    is_active     = db.Column(db.Boolean, default=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    commissions = db.relationship('ReferralCommission', backref='agent', lazy=True, cascade='all, delete-orphan')


class ReferralCommission(db.Model):
    __tablename__ = 'referral_commissions'

    id         = db.Column(db.Integer, primary_key=True)
    agent_id   = db.Column(db.Integer, db.ForeignKey('referral_agents.id', ondelete='CASCADE'), nullable=False)
    purchase_id= db.Column(db.Integer, db.ForeignKey('purchases.id', ondelete='CASCADE'), nullable=False)
    book_id    = db.Column(db.Integer, db.ForeignKey('books.id',  ondelete='CASCADE'), nullable=False)
    buyer_id   = db.Column(db.Integer, db.ForeignKey('users.id',  ondelete='CASCADE'), nullable=False)
    amount_earned = db.Column(db.Float, nullable=False)   # price_naira * rate
    is_paid    = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


def attribute_referral(purchase, ref_code):
    """
    Called after a payment succeeds. If ref_code is valid and not self-referral,
    creates a ReferralCommission row. Safe to call multiple times (idempotent).
    """
    if not ref_code:
        return
    agent = ReferralAgent.query.filter_by(ref_code=ref_code, is_active=True).first()
    if not agent:
        return
    # Prevent self-referral (agent buying their own link)
    from models import User
    buyer = User.query.get(purchase.user_id)
    if buyer and buyer.email == agent.email:
        return
    # Idempotent — don't double-credit
    exists = ReferralCommission.query.filter_by(purchase_id=purchase.id).first()
    if exists:
        return
    book = Book.query.get(purchase.book_id)
    if not book:
        return
    commission = ReferralCommission(
        agent_id=agent.id,
        purchase_id=purchase.id,
        book_id=purchase.book_id,
        buyer_id=purchase.user_id,
        amount_earned=round(purchase.amount_paid * REFERRAL_COMMISSION_RATE, 2)
    )
    db.session.add(commission)
    # db.session.commit() is intentionally omitted — caller commits
