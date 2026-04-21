"""
iGlobals Educational Services - Database Models
"""

from extensions import db
from flask_login import UserMixin
from datetime import datetime


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    session_token = db.Column(db.String(64), nullable=True)   # single-device enforcement
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    reviews = db.relationship('Review', backref='user', lazy=True, cascade='all, delete-orphan')
    favorites = db.relationship('Favorite', backref='user', lazy=True, cascade='all, delete-orphan')
    purchases = db.relationship('Purchase', backref='user', lazy=True, cascade='all, delete-orphan')
    notes = db.relationship('Note', backref='user', lazy=True, cascade='all, delete-orphan')
    library_items = db.relationship('LibraryItem', backref='user', lazy=True, cascade='all, delete-orphan')
    otp_codes = db.relationship('OTPCode', backref='user', lazy=True, cascade='all, delete-orphan')


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
    chapters = db.Column(db.JSON)
    content = db.Column(db.JSON)
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
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'book_id', name='unique_purchase'),)


class LibraryItem(db.Model):
    __tablename__ = 'library_items'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id', ondelete='CASCADE'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'book_id', name='unique_library_item'),)


class Note(db.Model):
    __tablename__ = 'notes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id', ondelete='CASCADE'), nullable=False)
    chapter_number = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class OTPCode(db.Model):
    __tablename__ = 'otp_codes'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    code = db.Column(db.String(6), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ── Referral System ───────────────────────────────────────────────────────

REFERRAL_COMMISSION_RATE = 0.10   # 10% — change here to update globally
REFERRAL_COOKIE_DAYS     = 5


class ReferralAgent(db.Model):
    __tablename__ = 'referral_agents'

    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(50), unique=True, nullable=False)
    first_name    = db.Column(db.String(80), nullable=False)
    email         = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
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
