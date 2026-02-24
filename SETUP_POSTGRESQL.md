# PostgreSQL Setup Guide for Windows

## Step 1: Install PostgreSQL

### Download and Install
1. Go to https://www.postgresql.org/download/windows/
2. Download the PostgreSQL installer (latest version recommended)
3. Run the installer
4. During installation:
   - Choose installation directory (default is fine)
   - Select components: PostgreSQL Server, pgAdmin 4, Command Line Tools
   - Set data directory (default is fine)
   - **Set a password for the postgres superuser** (REMEMBER THIS!)
   - Port: 5432 (default)
   - Locale: Default locale

### Verify Installation
Open Command Prompt and run:
```cmd
psql --version
```

If you get an error, add PostgreSQL to your PATH:
1. Search for "Environment Variables" in Windows
2. Edit "Path" in System Variables
3. Add: `C:\Program Files\PostgreSQL\15\bin` (adjust version number)

## Step 2: Create Database

### Option A: Using Command Line
```cmd
# Login as postgres user
psql -U postgres

# Create database
CREATE DATABASE iglobals_db;

# Create a new user (optional but recommended)
CREATE USER iglobals_user WITH PASSWORD 'your_password_here';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE iglobals_db TO iglobals_user;

# Exit
\q
```

### Option B: Using pgAdmin 4
1. Open pgAdmin 4 (installed with PostgreSQL)
2. Connect to PostgreSQL server (use password you set during installation)
3. Right-click "Databases" → "Create" → "Database"
4. Name: `iglobals_db`
5. Click "Save"

## Step 3: Configure Flask Application

### Create .env file
Create a file named `.env` in your project root:

```env
# Flask Configuration
SECRET_KEY=your-secret-key-change-this-in-production-make-it-long-and-random
FLASK_ENV=development

# Database Configuration
# Format: postgresql://username:password@localhost/database_name
DATABASE_URL=postgresql://postgres:your_postgres_password@localhost/iglobals_db

# Or if you created a custom user:
# DATABASE_URL=postgresql://iglobals_user:your_password_here@localhost/iglobals_db

# Paystack Configuration (get from https://paystack.com)
PAYSTACK_PUBLIC_KEY=pk_test_your_public_key_here
PAYSTACK_SECRET_KEY=sk_test_your_secret_key_here
```

## Step 4: Install Python Dependencies

```cmd
pip install -r requirements.txt
```

## Step 5: Initialize Database

### Create all tables
```cmd
python
```

Then in Python:
```python
from app import app, db
with app.app_context():
    db.create_all()
    print("Database tables created!")
exit()
```

### Seed with sample data
```cmd
python seed_data.py
```

### Create admin user
```cmd
python
```

Then in Python:
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
    print("Admin user created!")
    print("Email: admin@iglobals.com")
    print("Password: admin123")
exit()
```

## Step 6: Run the Application

```cmd
python app.py
```

Visit:
- Main site: http://localhost:5000
- Admin panel: http://localhost:5000/admin
  - Email: admin@iglobals.com
  - Password: admin123

## Common PostgreSQL Commands

### Connect to database
```cmd
psql -U postgres -d iglobals_db
```

### List all databases
```sql
\l
```

### List all tables
```sql
\dt
```

### View table structure
```sql
\d table_name
```

### View all users
```sql
SELECT * FROM users;
```

### View all books
```sql
SELECT id, title, author, category, is_free FROM books;
```

### Count records
```sql
SELECT COUNT(*) FROM books;
SELECT COUNT(*) FROM users WHERE is_admin = false;
```

### Delete all data (careful!)
```sql
TRUNCATE TABLE books CASCADE;
TRUNCATE TABLE users CASCADE;
```

### Drop database (careful!)
```sql
DROP DATABASE iglobals_db;
```

## Interacting with Database via Flask

### Using Flask Shell
```cmd
flask shell
```

Or with Python:
```cmd
python
```

```python
from app import app, db
from models import User, Book, Purchase, Review

# Must use app context
with app.app_context():
    # Get all books
    books = Book.query.all()
    for book in books:
        print(f"{book.id}: {book.title} by {book.author}")
    
    # Get specific book
    book = Book.query.get(1)
    print(book.title)
    
    # Filter books
    free_books = Book.query.filter_by(is_free=True).all()
    science_books = Book.query.filter_by(category='Science').all()
    
    # Get all users
    users = User.query.all()
    
    # Get user by email
    user = User.query.filter_by(email='admin@iglobals.com').first()
    
    # Get user's purchases
    purchases = Purchase.query.filter_by(user_id=user.id, payment_status='success').all()
    
    # Create new book
    new_book = Book(
        title='New Book Title',
        author='Author Name',
        category='Science',
        description='Book description',
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
    
    # Get statistics
    total_books = Book.query.count()
    total_users = User.query.filter_by(is_admin=False).count()
    total_revenue = db.session.query(db.func.sum(Purchase.amount_paid)).filter_by(payment_status='success').scalar()
    
    print(f"Total Books: {total_books}")
    print(f"Total Users: {total_users}")
    print(f"Total Revenue: ₦{total_revenue:,.2f}")
```

## Backup and Restore

### Backup database
```cmd
pg_dump -U postgres iglobals_db > backup.sql
```

### Restore database
```cmd
psql -U postgres iglobals_db < backup.sql
```

## Troubleshooting

### Can't connect to PostgreSQL
1. Check if PostgreSQL service is running:
   - Open Services (services.msc)
   - Look for "postgresql-x64-15" (or your version)
   - Make sure it's running

2. Check connection string in .env file
3. Verify password is correct

### "relation does not exist" error
Run:
```python
from app import app, db
with app.app_context():
    db.create_all()
```

### Port 5432 already in use
Another PostgreSQL instance is running. Either:
1. Stop the other instance
2. Change port in postgresql.conf
3. Use different port in DATABASE_URL

### Permission denied
Make sure your user has proper privileges:
```sql
GRANT ALL PRIVILEGES ON DATABASE iglobals_db TO your_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_user;
```

## Security Best Practices

1. **Never commit .env file** - Add to .gitignore
2. **Use strong passwords** for database users
3. **Change default admin password** after first login
4. **Use environment variables** for production
5. **Regular backups** of your database
6. **Limit database user privileges** in production

## Production Deployment

For production (e.g., Heroku, Railway, Render):

1. They usually provide DATABASE_URL automatically
2. Update your .env or environment variables
3. Run migrations:
```cmd
python
from app import app, db
with app.app_context():
    db.create_all()
```

4. Seed data if needed:
```cmd
python seed_data.py
```

5. Create admin user as shown in Step 5
