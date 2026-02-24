# iGlobals Educational Services - Complete Flask Application

A comprehensive educational platform for JUPEB exam preparation with secure content delivery, payment integration, user management, and full admin dashboard.

## Features

### User Features
- **User Authentication**: Secure signup/login with Flask-Login
- **Book Library**: Browse and search educational resources by category
- **Secure Reading**: Anti-screenshot and anti-print protection for premium content
- **Payment Integration**: Paystack payment gateway for premium books
- **Favorites**: Add books to favorites
- **Reviews & Ratings**: Write reviews and rate books (1-5 stars)
- **Notes**: Take personal notes while reading
- **Progress Tracking**: Track reading progress per chapter

### Admin Features
- **Dashboard**: Overview of books, users, purchases, and revenue
- **Book Management**:
  - Create books with rich text editor (Quill.js)
  - Edit book content and chapters
  - Delete books
  - View purchases per book
  - Support for chapter-based or whole content input
  - Auto-split whole content into chapters
- **User Management**:
  - View all users
  - See user purchase history
  - View user reviews
  - Track user spending
- **Review Management**:
  - View all reviews
  - Delete inappropriate reviews
- **Purchase Tracking**:
  - View all purchases
  - Track revenue per book
  - See payment references

### Security Features
- **Content Protection** (`static/js/security.js`):
  - Blocks screenshots (PrintScreen, Cmd+Shift+3/4)
  - Disables right-click context menu
  - Prevents text selection and copying
  - Blocks printing (Ctrl+P and print dialog)
  - Detects and blocks developer tools (F12, Ctrl+Shift+I)
  - Blurs content when window loses focus
  - Adds dynamic timestamp watermark
  - Prevents view source (Ctrl+U) and save (Ctrl+S)
- Security active only on library.html and reading.html

## Tech Stack

- **Backend**: Flask 3.0
- **Database**: PostgreSQL
- **ORM**: SQLAlchemy
- **Authentication**: Flask-Login
- **Frontend**: Tailwind CSS, Lucide Icons
- **Rich Text Editor**: Quill.js
- **Payment**: Paystack API

## Project Structure

```
├── app.py                          # Main Flask application
├── models.py                       # Database models
├── routes.py                       # User routes
├── admin_routes.py                 # Admin routes
├── seed_data.py                    # Database seeding
├── requirements.txt                # Python dependencies
├── .env                            # Environment variables (create this)
├── .env.example                    # Environment template
├── README.md                       # This file
├── SETUP_POSTGRESQL.md             # PostgreSQL setup guide
├── static/
│   ├── js/
│   │   └── security.js             # Content protection
│   └── logo.png                    # Application logo
└── templates/
    ├── layout.html                 # Base template
    ├── index.html                  # Homepage
    ├── about.html                  # About page
    ├── search.html                 # Search page
    ├── library.html                # User library (secured)
    ├── reading.html                # Reading page (secured)
    ├── login.html                  # Login page
    ├── signup.html                 # Signup page
    ├── forgot_password.html        # Password reset
    ├── payment.html                # Payment page
    └── admin/
        ├── layout.html             # Admin base template
        ├── dashboard.html          # Admin dashboard
        ├── books.html              # Books management
        ├── create_book.html        # Create book with editor
        ├── edit_book.html          # Edit book
        ├── book_purchases.html     # Book purchase history
        ├── reviews.html            # Reviews management
        ├── users.html              # Users list
        ├── user_detail.html        # User details
        └── settings.html           # Admin settings
```

## Quick Start

### 1. Install PostgreSQL
See [SETUP_POSTGRESQL.md](SETUP_POSTGRESQL.md) for detailed instructions.

**Quick version:**
- Download from https://www.postgresql.org/download/windows/
- Install with default settings
- Remember the postgres password!

### 2. Create Database
```cmd
psql -U postgres
CREATE DATABASE iglobals_db;
\q
```

### 3. Install Dependencies
```cmd
pip install -r requirements.txt
```

### 4. Configure Environment
Create `.env` file (copy from `.env.example`):
```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://postgres:your_password@localhost/iglobals_db
PAYSTACK_PUBLIC_KEY=pk_test_your_key
PAYSTACK_SECRET_KEY=sk_test_your_key
```

### 5. Initialize Database
```cmd
python
```
```python
from app import app, db
with app.app_context():
    db.create_all()
exit()
```

### 6. Seed Sample Data
```cmd
python seed_data.py
```

### 7. Create Admin User
```cmd
python
```
```python
from app import app, db
from models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    admin = User(
        full_name='Admin User',
        email='admin@iglobals.com',
        password_hash=generate_password_hash('admin123'),
        is_admin=True
    )
    db.session.add(admin)
    db.session.commit()
    print("Admin created: admin@iglobals.com / admin123")
exit()
```

### 8. Run Application
```cmd
python app.py
```

Visit:
- **Main Site**: http://localhost:5000
- **Admin Panel**: http://localhost:5000/admin
  - Email: `admin@iglobals.com`
  - Password: `admin123`

## Database Models

### User
- `id`: Primary key
- `full_name`: User's full name
- `email`: Unique email address
- `password_hash`: Hashed password
- `is_admin`: Boolean (admin flag)
- `created_at`: Registration date

### Book
- `id`: Primary key
- `title`: Book title
- `author`: Author name
- `category`: Science, Commercial, Arts, JUPEB, Past Questions
- `description`: Book description
- `image_url`: Cover image URL
- `price_naira`: Price in Naira (0 = free)
- `is_free`: Boolean flag
- `chapters`: JSON array of chapter titles
- `content`: JSON array of chapter content (HTML)
- `created_at`: Creation date

### Review
- `id`: Primary key
- `user_id`: Foreign key to User
- `book_id`: Foreign key to Book
- `rating`: 1-5 stars
- `comment`: Review text
- `likes`: Like count
- `dislikes`: Dislike count
- `created_at`: Review date

### Favorite
- `id`: Primary key
- `user_id`: Foreign key to User
- `book_id`: Foreign key to Book
- `created_at`: Date added

### Purchase
- `id`: Primary key
- `user_id`: Foreign key to User
- `book_id`: Foreign key to Book
- `amount_paid`: Amount in Naira
- `payment_reference`: Paystack reference
- `payment_status`: pending, success, failed
- `created_at`: Purchase date

### Note
- `id`: Primary key
- `user_id`: Foreign key to User
- `book_id`: Foreign key to Book
- `chapter_number`: Chapter index
- `content`: Note text
- `created_at`: Note date

## API Endpoints

### User APIs
- `POST /api/favorite/<book_id>` - Toggle favorite
- `POST /api/review/<book_id>` - Add review
- `POST /api/review/<review_id>/like` - Like review
- `POST /api/review/<review_id>/dislike` - Dislike review
- `POST /api/note/<book_id>` - Add note
- `POST /api/payment/initialize` - Initialize Paystack payment
- `GET /api/payment/verify/<reference>` - Verify payment

### Admin Routes
- `GET /admin` - Dashboard
- `GET /admin/books` - Books list
- `GET /admin/books/create` - Create book form
- `POST /admin/books/create` - Create book
- `GET /admin/books/<id>/edit` - Edit book form
- `POST /admin/books/<id>/edit` - Update book
- `POST /admin/books/<id>/delete` - Delete book
- `GET /admin/books/<id>/purchases` - Book purchases
- `GET /admin/reviews` - All reviews
- `POST /admin/reviews/<id>/delete` - Delete review
- `GET /admin/users` - Users list
- `GET /admin/users/<id>` - User details
- `GET /admin/settings` - Settings page

## Admin Dashboard Features

### Creating Books
1. Go to Admin → Books → Create New Book
2. Fill in basic information (title, author, category, price)
3. Choose content type:
   - **By Chapters**: Add chapters one by one with rich text editor
   - **Whole Content**: Paste entire content, system auto-splits by chapter markers
4. Use rich text editor for formatting:
   - Headers (H1, H2, H3)
   - Bold, Italic, Underline
   - Lists (ordered, unordered)
   - Links
5. Click "Create Book"

### Editing Books
1. Go to Admin → Books
2. Click edit icon on any book
3. Modify any field
4. Add/remove chapters
5. Edit content with rich text editor
6. Click "Update Book"

### Managing Reviews
1. Go to Admin → Reviews
2. View all reviews with ratings
3. Delete inappropriate reviews
4. Click user name to see user details

### Viewing Purchases
1. Go to Admin → Books
2. Click "View Purchases" on any book
3. See all users who purchased
4. View total revenue for that book

### User Management
1. Go to Admin → Users
2. View all registered users
3. Click on user to see:
   - Purchase history
   - Reviews written
   - Total amount spent

## Payment Flow

1. User clicks "Read Now" on premium book
2. If not purchased → redirect to payment page
3. User clicks "Pay Securely"
4. Paystack checkout opens
5. User completes payment
6. Payment verified via Paystack API
7. Purchase record created in database
8. User redirected to reading page

## Security Notes

- Security features are **deterrents**, not absolute protection
- For production:
  - Use strong `SECRET_KEY`
  - Use secure `DATABASE_URL`
  - Enable HTTPS
  - Configure Paystack webhooks
  - Add rate limiting
  - Implement logging
- Change default admin password immediately
- Never commit `.env` file

## Database Interaction

See [SETUP_POSTGRESQL.md](SETUP_POSTGRESQL.md) for detailed PostgreSQL commands and Flask database interaction examples.

**Quick examples:**
```python
from app import app, db
from models import Book, User, Purchase

with app.app_context():
    # Get all books
    books = Book.query.all()
    
    # Get free books
    free_books = Book.query.filter_by(is_free=True).all()
    
    # Get book by ID
    book = Book.query.get(1)
    
    # Count users
    user_count = User.query.filter_by(is_admin=False).count()
    
    # Total revenue
    revenue = db.session.query(db.func.sum(Purchase.amount_paid)).filter_by(payment_status='success').scalar()
```

## Troubleshooting

### Can't connect to database
- Check PostgreSQL is running (Services → postgresql)
- Verify DATABASE_URL in .env
- Check password is correct

### Tables don't exist
```python
from app import app, db
with app.app_context():
    db.create_all()
```

### Admin can't login
Make sure admin user was created with `is_admin=True`

### Payment not working
- Check Paystack keys in .env
- Use test keys for development
- Check Paystack dashboard for errors

## Production Deployment

1. Set environment variables (don't use .env in production)
2. Use production DATABASE_URL
3. Set `FLASK_ENV=production`
4. Use production Paystack keys
5. Enable HTTPS
6. Configure Paystack webhooks
7. Set up database backups
8. Add logging and monitoring

## Sample Data

After running `seed_data.py`, you'll have 6 books:
1. **Scientific Inquiries Vol. I** (₦5,000 - Premium)
2. **Business Analytics Mastery** (₦4,500 - Premium)
3. **Creative Strategies in Literature** (₦4,000 - Premium)
4. **JUPEB Mastery Complete Guide** (Free)
5. **JUPEB Past Questions & Answers** (₦3,500 - Premium)
6. **Chemistry & Biology Breakdown** (Free)

## License

Copyright © 2026 iGlobals Educational Services. All rights reserved.
