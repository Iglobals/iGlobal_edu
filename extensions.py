"""
Flask extensions initialization
This file prevents circular imports by initializing extensions separately
"""
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from pymongo import MongoClient

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'login'

mongo_client = None


def init_mongo(app):
    """Same pattern as iTest's app/extensions.py - book/chapter/page CONTENT
    lives here going forward; book metadata (title, price, etc.) stays in
    Postgres via SQLAlchemy above. See mongo_books.py."""
    global mongo_client
    uri = app.config.get('MONGODB_URI')
    if uri:
        mongo_client = MongoClient(uri)
        try:
            app.mongo = mongo_client.get_database()
        except Exception:
            app.mongo = mongo_client.get_database('iglobals_edu')

        from mongo_books import ensure_indexes
        ensure_indexes(app.mongo)
    else:
        app.mongo = None
