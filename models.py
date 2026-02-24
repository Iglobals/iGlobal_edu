"""
iGlobals Educational Services - Database Models
"""

from extensions import db
from flask_login import UserMixin
from datetime import datetime

# ============================================================
# USER MODEL
# ============================================================

class User(UserMixin, db.Model):
    """User account model"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    reviews = db.relationship('Review', backref='user', lazy=True, cascade='all, delete-orphan')
    favorites = db.relationship('Favorite', backref='user', lazy=True, cascade='all, delete-orphan')
    purchases = db.relationship('Purchase', backref='user', lazy=True, cascade='all, delete-orphan')
    notes = db.relationship('Note', backref='user', lazy=True, cascade='all, delete-orphan')
    library_items = db.relationship('LibraryItem', backref='user', lazy=True, cascade='all, delete-orphan')

# ============================================================
# BOOK MODEL
# ============================================================

class Book(db.Model):
    """Book/Study material model"""
    __tablename__ = 'books'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)  # Science, Commercial, Arts, JUPEB, Past Questions
    description = db.Column(db.Text)
    image_url = db.Column(db.String(500))
    price_naira = db.Column(db.Float, default=0.0)  # 0 = free
    is_free = db.Column(db.Boolean, default=False)
    chapters = db.Column(db.JSON)  # List of chapter titles
    content = db.Column(db.JSON)  # List of chapter content (HTML)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    reviews = db.relationship('Review', backref='book', lazy=True, cascade='all, delete-orphan')
    favorites = db.relationship('Favorite', backref='book', lazy=True, cascade='all, delete-orphan')
    purchases = db.relationship('Purchase', backref='book', lazy=True, cascade='all, delete-orphan')
    notes = db.relationship('Note', backref='book', lazy=True, cascade='all, delete-orphan')
    library_items = db.relationship('LibraryItem', backref='book', lazy=True, cascade='all, delete-orphan')

# ============================================================
# REVIEW MODEL
# ============================================================

class Review(db.Model):
    """Book review model"""
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5
    comment = db.Column(db.Text)
    likes = db.Column(db.Integer, default=0)
    dislikes = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ============================================================
# FAVORITE MODEL
# ============================================================

class Favorite(db.Model):
    """User's favorite books model"""
    __tablename__ = 'favorites'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'book_id', name='unique_favorite'),)

# ============================================================
# PURCHASE MODEL
# ============================================================

class Purchase(db.Model):
    """Book purchase transaction model"""
    __tablename__ = 'purchases'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    amount_paid = db.Column(db.Float, nullable=False)
    payment_reference = db.Column(db.String(100), unique=True)
    payment_status = db.Column(db.String(20), default='pending')  # pending, success, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'book_id', name='unique_purchase'),)

# ============================================================
# LIBRARY ITEM MODEL
# ============================================================

class LibraryItem(db.Model):
    """Books added to user's library (not necessarily purchased)"""
    __tablename__ = 'library_items'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('user_id', 'book_id', name='unique_library_item'),)

# ============================================================
# NOTE MODEL
# ============================================================

class Note(db.Model):
    """User study notes model"""
    __tablename__ = 'notes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    chapter_number = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)