# iGlobals Educational Services - Complete Implementation Guide

## 🎉 What Has Been Built

You now have a **complete, production-ready Flask application** with:

### ✅ User Features
- User registration and authentication
- Browse and search books by category
- Add books to favorites
- Purchase premium books via Paystack
- Read books with chapter navigation
- Write reviews and ratings
- Take personal notes while reading
- Secure content protection (anti-screenshot, anti-print)

### ✅ Admin Dashboard
- Complete admin panel at `/admin`
- Dashboard with statistics (books, users, revenue, purchases)
- **Book Management**:
  - Create books with rich text editor (Quill.js)
  - Edit existing books
  - Delete books
  - View purchases per book
  - Two content input modes:
    - **By Chapters**: Add chapters individually
    - **Whole Content**: Paste entire content, auto-splits into chapters
- **User Management**:
  - View all users
  - See user purchase history
  - View user reviews
  - Track spending per user
- **Review Management**:
  - View all reviews
  - Delete inappropriate reviews
- **Purchase Tracking**:
  - View all purchases
  - Revenue tracking
  - Payment references

### ✅ Security Features
- Content protection on library and reading pages
- Prevents screenshots, printing, right-click, text selection
- Detects developer tools
- Blurs content on window focus loss
- Dynamic watermark

### ✅ Database
- PostgreSQL with 6 models
- Relationships properly configured
- Sample data seeding script
- Easy database interaction via Flask

## 📁 Complete File Structure

```
iglobals-flask/
├── app.py                          # Main Flask app
├── models.py                       # Database models (User, Book, Review, etc.)
├── routes.py                       # User-facing routes
├── admin_routes.py                 # Admin routes
├── seed_data.py                    # Sample data seeding
├── setup.py                        # Quick setup script
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment template
├── README.md                       # Main documentation
├── SETUP_POSTGRESQL.md             # PostgreSQL guide
├── COMPLETE_GUIDE.md               # This file
├── static/
│   ├── js/
│   │   └── security.js             # Content protection
│   └── logo.png                    # Your logo (copy here)
└── templates/
    ├── layout.html                 # Base template
    ├── index.html                  # Homepage ✅
    ├── about.html                  # About page ✅
    ├── search.html                 # Search page ✅
    ├── library.html                # User library ✅ (secured)
    ├── reading.html                # Reading page ✅ (secured)
    ├── login.html                  # Login ✅
    ├── signup.html                 # Signup ✅
    ├── forgot_password.html        # Password reset ✅
    ├── payment.html                # Payment page ✅
    └── admin/
        ├── layout.html             # Admin base ✅
        ├── dashboard.html          # Dashboard ✅
        ├── books.html              # Books list ✅
        ├── create_book.html        # Create book ✅
        ├── edit_book.html          # Edit book ✅
        ├── book_purchases.html     # Purchase history ✅
        ├── reviews.html            # Reviews ✅
        ├── users.html              # Users list ✅
        ├── user_detail.html        # User details ✅
        └── settings.html           # Settings ✅
```

## 🚀 Quick Start (5 Minutes)

### 1. Install PostgreSQL
Download from: https://www.postgresql.org/download/windows/
- Install with default settings
- Remember the postgres password!

### 2. Create Database
```cmd
psql -U postgres
CREATE DATABASE iglobals_db;
\q
```

### 3. Install Python Dependencies
```cmd
pip install -r requirements.txt
```

### 4. Create .env File
Copy `.env.example` to `.env` and fill in:
```env
SECRET_KEY=make-this-long-and-random-abc123xyz789
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost/iglobals_db
PAYSTACK_PUBLIC_KEY=pk_test_your_key
PAYSTACK_SECRET_KEY=sk_test_your_key
```

### 5. Run Setup Script
```cmd
python setup.py
```

This will:
- Create all database tables
- Create admin user (admin@iglobals.com / admin123)
- Optionally seed sample books

### 6. Start Application
```cmd
python app.py
```

### 7. Access Application
- **Main Site**: http://localhost:5000
- **Admin Panel**: http://localhost:5000/admin
  - Email: `admin@iglobals.com`
  - Password: `admin123`

## 📚 How to Use Admin Dashboard

### Creating a Book

1. **Login to Admin**
   - Go to http://localhost:5000/admin
   - Login with admin credentials

2. **Navigate to Books**
   - Click "Books" in sidebar
   - Click "Create New Book"

3. **Fill Basic Information**
   - Title: e.g., "Advanced Physics"
   - Author: e.g., "Dr. John Doe"
   - Category: Select from dropdown
   - Image URL: Paste image URL (e.g., from Unsplash)
   - Description: Brief description
   - Price: Enter price in Naira (or 0 for free)
   - Check "Mark as Free" if applicable

4. **Choose Content Type**

   **Option A: By Chapters** (Recommended)
   - Select "By Chapters"
   - For each chapter:
     - Enter chapter title (e.g., "Chapter 1: Introduction")
     - Use rich text editor to format content
     - Click "Add Another Chapter" for more
   
   **Option B: Whole Content** (Auto-split)
   - Select "Whole Content (Auto-split)"
   - Paste entire book content
   - System will automatically detect chapters based on:
     - "Chapter 1: Title"
     - "CHAPTER 1 - Title"
     - "Ch. 1: Title"
   - If no chapters detected, creates single chapter

5. **Use Rich Text Editor**
   - **Headers**: Select H1, H2, or H3 for headings
   - **Bold/Italic/Underline**: Format text
   - **Lists**: Create ordered or bullet lists
   - **Links**: Add hyperlinks
   - **Clean**: Remove formatting

6. **Save Book**
   - Click "Create Book"
   - Book appears in books list
   - Users can now see and purchase it

### Editing a Book

1. Go to Admin → Books
2. Click edit icon (pencil) on any book
3. Modify any field
4. Add/remove chapters
5. Edit content with rich text editor
6. Click "Update Book"

### Viewing Book Purchases

1. Go to Admin → Books
2. Click "View Purchases" (eye icon) on any book
3. See:
   - Total sales count
   - Total revenue
   - List of all purchasers
   - Purchase dates and references

### Managing Reviews

1. Go to Admin → Reviews
2. View all reviews with:
   - User name
   - Book title
   - Rating (stars)
   - Comment
   - Date
3. Delete inappropriate reviews

### Managing Users

1. Go to Admin → Users
2. View all registered users
3. Click on user to see:
   - Total amount spent
   - All purchased books
   - All reviews written

## 🔐 Security Implementation

### Where Security is Active
- **library.html**: User's book library
- **reading.html**: Book reading page

### What is Protected
1. **Screenshots**: Blocks PrintScreen, Cmd+Shift+3/4
2. **Printing**: Blocks Ctrl+P and print dialog
3. **Right-click**: Disabled
4. **Text Selection**: Disabled
5. **Developer Tools**: Detects F12, Ctrl+Shift+I
6. **View Source**: Blocks Ctrl+U
7. **Save Page**: Blocks Ctrl+S
8. **Window Blur**: Blurs content when window loses focus
9. **Watermark**: Dynamic timestamp overlay

### How It Works
The `static/js/security.js` script is loaded only on library.html and reading.html via:
```html
{% block extra_js %}
<script src="{{ url_for('static', filename='js/security.js') }}"></script>
{% endblock %}
```

## 💳 Payment Integration

### Setup Paystack

1. **Create Account**
   - Go to https://paystack.com
   - Sign up for free account

2. **Get API Keys**
   - Go to Settings → API Keys & Webhooks
   - Copy Test Public Key (starts with `pk_test_`)
   - Copy Test Secret Key (starts with `sk_test_`)

3. **Add to .env**
   ```env
   PAYSTACK_PUBLIC_KEY=pk_test_your_key_here
   PAYSTACK_SECRET_KEY=sk_test_your_key_here
   ```

### Payment Flow

1. User clicks "Read Now" on premium book
2. If not purchased → redirects to payment page
3. User clicks "Pay Securely"
4. Paystack checkout modal opens
5. User enters card details (use test cards)
6. Payment processed
7. Payment verified
8. Purchase record created
9. User redirected to reading page

### Test Cards (Paystack)
```
Success: 4084084084084081
Decline: 4084080000000408
CVV: 408
PIN: 0000
Expiry: Any future date
```

## 🗄️ Database Interaction

### Using Python Shell

```cmd
python
```

```python
from app import app, db
from models import User, Book, Purchase, Review

with app.app_context():
    # Get all books
    books = Book.query.all()
    for book in books:
        print(f"{book.id}: {book.title} - ₦{book.price_naira}")
    
    # Get free books
    free_books = Book.query.filter_by(is_free=True).all()
    
    # Get book by ID
    book = Book.query.get(1)
    print(f"Title: {book.title}")
    print(f"Author: {book.author}")
    print(f"Chapters: {len(book.chapters)}")
    
    # Get all users (non-admin)
    users = User.query.filter_by(is_admin=False).all()
    
    # Get user purchases
    user = User.query.get(1)
    purchases = Purchase.query.filter_by(user_id=user.id, payment_status='success').all()
    
    # Calculate total revenue
    total_revenue = db.session.query(db.func.sum(Purchase.amount_paid)).filter_by(payment_status='success').scalar()
    print(f"Total Revenue: ₦{total_revenue:,.2f}")
    
    # Create new book
    new_book = Book(
        title='New Book',
        author='Author Name',
        category='Science',
        description='Description here',
        image_url='https://example.com/image.jpg',
        price_naira=5000.0,
        is_free=False,
        chapters=['Chapter 1', 'Chapter 2'],
        content=['<p>Content 1</p>', '<p>Content 2</p>']
    )
    db.session.add(new_book)
    db.session.commit()
    
    # Update book
    book = Book.query.get(1)
    book.price_naira = 6000.0
    db.session.commit()
    
    # Delete book
    book = Book.query.get(1)
    db.session.delete(book)
    db.session.commit()
```

### Using PostgreSQL Directly

```cmd
psql -U postgres -d iglobals_db
```

```sql
-- View all books
SELECT id, title, author, category, price_naira, is_free FROM books;

-- View all users
SELECT id, full_name, email, is_admin FROM users;

-- View purchases
SELECT u.full_name, b.title, p.amount_paid, p.created_at 
FROM purchases p
JOIN users u ON p.user_id = u.id
JOIN books b ON p.book_id = b.id
WHERE p.payment_status = 'success';

-- Count books by category
SELECT category, COUNT(*) FROM books GROUP BY category;

-- Total revenue
SELECT SUM(amount_paid) FROM purchases WHERE payment_status = 'success';
```

## 🐛 Troubleshooting

### Can't connect to database
```
Error: could not connect to server
```
**Solution:**
1. Check PostgreSQL is running (Services → postgresql)
2. Verify DATABASE_URL in .env
3. Check password is correct

### Tables don't exist
```
Error: relation "books" does not exist
```
**Solution:**
```python
from app import app, db
with app.app_context():
    db.create_all()
```

### Admin can't login
**Solution:**
Make sure admin was created with `is_admin=True`:
```python
from app import app, db
from models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    admin = User.query.filter_by(email='admin@iglobals.com').first()
    if admin:
        admin.is_admin = True
        db.session.commit()
```

### Payment not working
**Solution:**
1. Check Paystack keys in .env
2. Use test keys for development
3. Check Paystack dashboard for errors
4. Use test card numbers

### Security script not working
**Solution:**
1. Check script is loaded in template
2. Open browser console for errors
3. Make sure lucide icons are loaded

## 📝 Common Tasks

### Change Admin Password
```python
from app import app, db
from models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    admin = User.query.filter_by(email='admin@iglobals.com').first()
    admin.password_hash = generate_password_hash('new_password')
    db.session.commit()
```

### Add Another Admin
```python
from app import app, db
from models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    new_admin = User(
        full_name='Another Admin',
        email='admin2@iglobals.com',
        password_hash=generate_password_hash('password123'),
        is_admin=True
    )
    db.session.add(new_admin)
    db.session.commit()
```

### Backup Database
```cmd
pg_dump -U postgres iglobals_db > backup.sql
```

### Restore Database
```cmd
psql -U postgres iglobals_db < backup.sql
```

### Clear All Data
```python
from app import app, db
from models import Book, User, Purchase, Review, Favorite, Note

with app.app_context():
    # Delete all records
    Book.query.delete()
    Purchase.query.delete()
    Review.query.delete()
    Favorite.query.delete()
    Note.query.delete()
    User.query.filter_by(is_admin=False).delete()
    db.session.commit()
```

## 🚀 Deployment

### For Production

1. **Environment Variables**
   - Don't use .env file
   - Set environment variables in hosting platform
   - Use production DATABASE_URL
   - Use production Paystack keys

2. **Database**
   - Use managed PostgreSQL (Heroku Postgres, Railway, etc.)
   - Run migrations
   - Create admin user

3. **Security**
   - Enable HTTPS
   - Set strong SECRET_KEY
   - Configure Paystack webhooks
   - Add rate limiting
   - Enable logging

4. **Hosting Options**
   - **Heroku**: Easy deployment, free tier available
   - **Railway**: Modern, easy to use
   - **Render**: Free tier, automatic deploys
   - **PythonAnywhere**: Python-specific hosting
   - **DigitalOcean**: More control, requires setup

## 📞 Support

If you encounter issues:

1. Check this guide
2. Check SETUP_POSTGRESQL.md
3. Check README.md
4. Review error messages carefully
5. Check PostgreSQL is running
6. Verify .env configuration
7. Check browser console for JavaScript errors

## 🎓 Learning Resources

- **Flask**: https://flask.palletsprojects.com/
- **SQLAlchemy**: https://docs.sqlalchemy.org/
- **PostgreSQL**: https://www.postgresql.org/docs/
- **Paystack**: https://paystack.com/docs/
- **Tailwind CSS**: https://tailwindcss.com/docs

## ✨ Features Summary

### What Users Can Do
✅ Sign up and login
✅ Browse books by category
✅ Search books
✅ Add books to favorites
✅ Purchase premium books
✅ Read books with chapter navigation
✅ Write reviews and ratings
✅ Take personal notes
✅ Adjust font size while reading
✅ Fullscreen reading mode

### What Admins Can Do
✅ View dashboard with statistics
✅ Create books with rich text editor
✅ Edit existing books
✅ Delete books
✅ View purchases per book
✅ Track total revenue
✅ Manage users
✅ View user purchase history
✅ Delete inappropriate reviews
✅ Auto-split whole content into chapters

### Security Features
✅ Anti-screenshot protection
✅ Anti-print protection
✅ Disable right-click
✅ Disable text selection
✅ DevTools detection
✅ Window blur on focus loss
✅ Dynamic watermark
✅ Secure payment processing

## 🎉 You're All Set!

Your complete educational platform is ready. You can now:

1. **Test the user experience**
   - Sign up as a user
   - Browse books
   - Purchase a book (use test card)
   - Read and take notes

2. **Test the admin panel**
   - Login as admin
   - Create a new book
   - Edit existing books
   - View statistics

3. **Customize**
   - Add your logo to `static/logo.png`
   - Modify colors in templates
   - Add more categories
   - Customize email templates

4. **Deploy**
   - Choose hosting platform
   - Set environment variables
   - Deploy and test

**Happy coding! 🚀**
