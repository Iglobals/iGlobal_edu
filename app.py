"""
iGlobals Educational Services - Flask Application
Main application file
"""

from flask import Flask
import os
from dotenv import load_dotenv
from extensions import db, login_manager, init_mongo
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

# MongoDB - book/chapter/page CONTENT only (see mongo_books.py). Book metadata
# (title, price, etc.) stays in Postgres above.
app.config['MONGODB_URI'] = os.environ.get('MONGODB_URI')

# Paystack configuration
app.config['PAYSTACK_PUBLIC_KEY'] = os.environ.get('PAYSTACK_PUBLIC_KEY', '')
app.config['PAYSTACK_SECRET_KEY'] = os.environ.get('PAYSTACK_SECRET_KEY', '')

# ICA centralized Paystack webhook relay (see ica_webhook_routes.py) - the
# secret ICA generated for THIS app specifically, from Settings > Clients >
# this app > Payment webhooks in the ICA admin panel. Not Paystack's own key.
app.config['ICA_WEBHOOK_RELAY_SECRET'] = os.environ.get('ICA_WEBHOOK_RELAY_SECRET', '')

# StudyNeat partner SSO (AI features integration - see studyneat_client.py)
app.config['STUDYNEAT_API_BASE_URL'] = os.environ.get('STUDYNEAT_API_BASE_URL', 'https://api.studyneat.xyz')
app.config['STUDYNEAT_CLIENT_KEY'] = os.environ.get('STUDYNEAT_CLIENT_KEY', '')
app.config['STUDYNEAT_CLIENT_SECRET'] = os.environ.get('STUDYNEAT_CLIENT_SECRET', '')

# iGlobals Central Auth (ICA) configuration
app.config['ICA_BASE_URL'] = os.environ.get('ICA_BASE_URL')
app.config['ICA_CLIENT_ID'] = os.environ.get('ICA_CLIENT_ID')
app.config['ICA_CLIENT_SECRET'] = os.environ.get('ICA_CLIENT_SECRET')
app.config['ICA_REDIRECT_URI'] = os.environ.get('ICA_REDIRECT_URI', 'http://localhost:5000/auth/callback')

# Cloudinary configuration
import cloudinary
cloudinary.config(
    cloud_name  = os.environ.get('CLOUDINARY_CLOUD_NAME', ''),
    api_key     = os.environ.get('CLOUDINARY_API_KEY', ''),
    api_secret  = os.environ.get('CLOUDINARY_API_SECRET', ''),
    secure      = True
)

# Initialize extensions with app
db.init_app(app)
login_manager.init_app(app)
init_mongo(app)
migrate = Migrate(app, db)

# Import models AFTER initializing db and login_manager
from models import User, Book, Review, Favorite, Purchase, Note, LibraryItem, SubscriptionPlan, Subscription, SubscriptionPayment

# User loader for Flask-Login (must be AFTER importing User model)
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Import routes AFTER importing models
from routes import *
import auth_routes
import admin_routes
import referral_routes
import subscription_routes
import studyneat_routes
import ica_webhook_routes

# Vercel handler
def handler(request):
    return app(request)

# app.run(debug=True, host='0.0.0.0', port=5000) // app.run()
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)