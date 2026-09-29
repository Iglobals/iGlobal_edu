# Quick Start Guide - iGlobals Platform

## 🚀 Getting Started

### 1. Database Setup
```bash
# Run migration to add LibraryItem table
python migrate_library.py

# Seed books with new pricing structure
python seed_data.py
```

### 2. Start the Application
```bash
# Development mode
python app.py

# Or with Flask CLI
flask run
```

### 3. Access the Platform
- **Frontend**: http://localhost:5000
- **Admin Panel**: http://localhost:5000/admin
- Login is via ICA (iGlobals Central Auth), not a local password - sign in once, then flag your account as admin in the database. See `README.md`'s Quick Start step 7 for the full steps.

## 📚 Book Management

### Adding Books via Admin Panel:
1. Login to admin panel
2. Go to "Books" → "Create New Book"
3. Fill in details:
   - Title, Author, Category
   - Description
   - Price (₦1,999 for individual, ₦4,999 for combinations)
   - Image URL (see IMAGE_GUIDE.md)
4. Add chapters with content
5. Save

### Getting Image URLs:
```
Quick Method:
1. Go to unsplash.com
2. Search "textbook" or subject name
3. Right-click image → Copy image address
4. Add ?w=600&q=80 to URL
5. Paste in Image URL field

Example:
https://images.unsplash.com/photo-1532094349884-543bc11b234d?w=600&q=80
```

### Editing Books:
1. Admin Panel → Books → Edit
2. Content is pre-populated in editors
3. Make changes
4. Save

## 👤 User Flow

### New User:
1. **Sign In** → via ICA (account is created automatically on first login)
2. **Browse** → Search page (no login required)
3. **Preview** → Click any book to see details
4. **Add to Library** → Click "Add to Library" button
5. **Purchase** → For paid books (₦1,999 or ₦4,999)
6. **Read** → Access full content

### Library Organization:
- **Added Books**: All books added (free or paid, purchased or not)
- **Your Books**: Books you can read (free + purchased)
- **Favorites**: Your favorite books from "Your Books"

## 💳 Payment Flow

### For Users:
1. Add book to library from preview page
2. Go to Library → Added Books
3. Click "Purchase" button
4. Complete Paystack payment
5. Automatically redirected to reading page
6. Start reading immediately

### For Testing:
Use Paystack test cards:
- Success: 4084084084084081
- Decline: 5060666666666666666

## 🎨 Color Scheme

### Primary Colors:
- **Dark Purple**: #2F1341 (buttons, links, primary actions)
- **Light Purple**: #4A1F5C (hover states)
- **Dark Orange**: #B0522E (secondary actions)
- **Light Orange**: #C86A3F (hover states)

### Usage:
- Primary buttons: Purple
- Secondary buttons: Orange
- Links: Purple
- Hover effects: Lighter shades

## 📱 Responsive Design

### Breakpoints:
- **Desktop**: 4 columns (books grid)
- **Tablet**: 3 columns
- **Mobile**: 1 column (single book per row)

### Mobile Features:
- Horizontal scrollable category tabs
- Optimized search bar (no zoom on focus)
- Touch-friendly buttons
- Consistent image sizes

## 🔐 Admin Features

### Dashboard:
- Total users, books, purchases
- Recent activity
- Quick stats

### Book Management:
- Create, edit, delete books
- Pre-populated editors
- Rich text content editing
- Chapter management

### User Management:
- View all users
- User details
- Purchase history

## ⚠️ Common Issues

### Database Connection Error:
```bash
# Check PostgreSQL is running
# Verify .env file has correct credentials
python testdb.py
```

### Images Not Showing:
- Check URL is direct image link
- Verify URL uses https://
- Test URL in browser
- See IMAGE_GUIDE.md

### Flash Messages Not Appearing:
- Check browser console for errors
- Verify JavaScript is enabled
- Clear browser cache

### Payment Failing:
- Check Paystack API keys in .env
- Verify test mode vs live mode
- Check network connectivity
- Review Paystack dashboard

## 📖 Documentation

### Available Guides:
- `LIBRARY_SYSTEM_GUIDE.md` - Complete system documentation
- `IMAGE_GUIDE.md` - How to get book cover images
- `CHANGES_SUMMARY.md` - Recent updates and changes
- `FINAL_UPDATES.md` - Latest improvements
- `QUICK_START.md` - This file

## 🛠️ Development

### Project Structure:
```
iGlobals/
├── app.py                 # Main application
├── routes.py              # Route handlers
├── models.py              # Database models
├── extensions.py          # Flask extensions
├── templates/             # HTML templates
│   ├── layout.html       # Base template
│   ├── index.html        # Home page
│   ├── search.html       # Search page
│   ├── library.html      # Library page
│   ├── preview.html      # Book preview
│   ├── reading.html      # Reading page
│   └── admin/            # Admin templates
├── static/               # Static files
│   ├── js/              # JavaScript
│   └── library-svgrepo-com.svg
├── seed_data.py          # Database seeding
└── migrate_library.py    # Database migration
```

### Key Files:
- **app.py**: Flask app initialization
- **routes.py**: All route handlers
- **models.py**: User, Book, Purchase, LibraryItem, etc.
- **extensions.py**: db, login_manager initialization

## 🎯 Quick Tasks

### Add a New Book:
```python
# Via seed_data.py
{
    'title': 'Book Title',
    'author': 'Author Name',
    'category': 'Science',
    'description': 'Book description',
    'image_url': 'https://images.unsplash.com/photo-XXXXX?w=600&q=80',
    'price_naira': 1999.0,
    'is_free': False,
    'chapters': ['Preface', 'Chapter 1', ...],
    'content': ['<p>Content...</p>', ...]
}
```

### Change Pricing:
Edit `seed_data.py`:
- Individual books: `price_naira: 1999.0`
- Combinations: `price_naira: 4999.0`
- Free books: `price_naira: 0.0, is_free: True`

### Update Colors:
Edit `templates/layout.html`:
```css
:root {
    --ig-purple: #2F1341;
    --ig-orange: #B0522E;
}
```

### Adjust Flash Message Timing:
Edit `templates/layout.html`:
```javascript
setTimeout(function() {
    dismissFlash(flash.querySelector('button'));
}, 3000);  // Change 3000 to desired milliseconds
```

## 📞 Support

### Need Help?
1. Check documentation files
2. Review browser console (F12)
3. Check server logs
4. Verify database connection
5. Test with different browsers

### Useful Commands:
```bash
# Check Python version
python --version

# Install dependencies
pip install -r requirements.txt

# Run tests
python testdb.py

# Reset database
python reset.py

# Seed data
python seed_data.py
```

## ✨ Features Summary

### User Features:
- Browse books without login
- Preview books (first 3-5 pages)
- Add books to library
- Purchase books via Paystack
- Read full content
- Add favorites
- Take notes

### Admin Features:
- Manage books (CRUD)
- Manage users
- View purchases
- Edit content with rich text editor
- Pre-populated editors

### System Features:
- Auto-dismissing flash messages
- Form validation with error styling
- Consistent book image sizes
- Mobile-responsive design
- Secure payment processing
- Access control

## 🎉 You're Ready!

The platform is fully set up and ready to use. Start by:
1. Running the migration
2. Seeding the database
3. Starting the application
4. Creating a test account
5. Exploring the features

Happy coding! 🚀
