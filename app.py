"""
iGlobals Educational Services - Flask Application
Main application file
"""

from flask import Flask
import os
from dotenv import load_dotenv
from extensions import db, login_manager
from flask_migrate import Migrate

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://localhost/iglobals_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,       # test connection before using it — drops stale ones
    'pool_recycle': 280,         # recycle connections before Neon's 300s idle timeout
    'pool_size': 5,
    'max_overflow': 2,
}

# Paystack configuration
app.config['PAYSTACK_PUBLIC_KEY'] = os.environ.get('PAYSTACK_PUBLIC_KEY', '')
app.config['PAYSTACK_SECRET_KEY'] = os.environ.get('PAYSTACK_SECRET_KEY', '')

# Initialize extensions with app
db.init_app(app)
login_manager.init_app(app)
migrate = Migrate(app, db)

# Import models AFTER initializing db and login_manager
from models import User, Book, Review, Favorite, Purchase, Note, LibraryItem, OTPCode

# User loader for Flask-Login (must be AFTER importing User model)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Import routes AFTER importing models
from routes import *
import admin_routes
import referral_routes

# Vercel handler
def handler(request):
    return app(request)

# app.run(debug=True, host='0.0.0.0', port=5000) // app.run()
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)