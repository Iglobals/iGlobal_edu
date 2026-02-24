# iGlobals Library System Guide

## Overview
The new library system separates book discovery, preview, library management, and full reading access into distinct workflows.

## Color Scheme
- **Primary Purple**: #2F1341 (Dark Purple)
- **Light Purple**: #4A1F5C (Hover states)
- **Primary Orange**: #B0522E (Secondary actions)
- **Light Orange**: #C86A3F (Hover states)

## User Flow

### 1. Discovery (Home & Search Pages)
- **Home Page**: Featured books with "Preview" buttons
- **Search Page**: All books with category filters
- **Action**: Click "Preview" to see book details
- **Access**: Available to all users (logged in or not)

### 2. Preview Page (`/preview/<book_id>`)
- **Content**:
  - Book details (title, author, category, price)
  - Full description
  - First 3-5 pages in a carousel/swipeable view
  - "Add to Library" button
- **Access**: Available to all users
- **Actions**:
  - Logged in: Can add book to library
  - Not logged in: Redirected to login

### 3. Library Page (`/library`)
Three filter tabs:

#### a. Added Books (Default)
- **Shows**: All books user has added to library
- **Includes**: Both free and paid books (purchased or not)
- **Actions**:
  - Preview button: View book preview
  - Purchase button: For unpurchased paid books
  - View/Read button: For free books or purchased books
- **Access**: Full reading only for free or purchased books

#### b. Your Books
- **Shows**: Books user can actually read
- **Includes**: Free books + Successfully purchased books
- **Actions**:
  - Continue Reading: Access full content
  - Add to Favorites: Mark as favorite
- **Access**: Full reading access to all books in this section

#### c. Favorites
- **Shows**: Subset of "Your Books" marked as favorites
- **Includes**: Only books from "Your Books" that user favorited
- **Actions**:
  - Continue Reading: Access full content
  - Remove from Favorites
- **Access**: Full reading access

### 4. Reading Page (`/reading/<book_id>`)
- **Access Control**:
  1. Book must be in user's library (LibraryItem exists)
  2. Book must be free OR user must have successful purchase
- **Features**:
  - Full book content
  - Notes and highlights
  - Reviews
- **Restrictions**: Cannot access by typing URL directly unless conditions met

## Database Models

### LibraryItem (New)
```python
class LibraryItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### Purchase (Existing)
```python
class Purchase(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'))
    amount_paid = db.Column(db.Float)
    payment_reference = db.Column(db.String(100), unique=True)
    payment_status = db.Column(db.String(20))  # pending, success, failed
```

### Favorite (Existing)
```python
class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'))
```

## API Endpoints

### `/api/library/add/<book_id>` (POST)
- Adds book to user's library
- Creates LibraryItem record
- Returns: `{status: 'added'|'already_added'}`

### `/api/favorite/<book_id>` (POST)
- Toggles favorite status
- **Requires**: Book in library AND (free OR purchased)
- Returns: `{status: 'added'|'removed'|'error'}`

### `/api/payment/initialize` (POST)
- Initializes Paystack payment
- Creates/updates Purchase record
- Returns: `{status: 'success', data: {...}, reference: '...'}`

### `/api/payment/verify/<reference>` (GET)
- Verifies Paystack payment
- Updates Purchase status to 'success'
- Adds book to library automatically
- Redirects to reading page on success

## Payment Flow

1. User clicks "Purchase" on Added Books
2. Redirected to `/payment/<book_id>`
3. Paystack modal opens
4. User completes payment
5. Paystack redirects to `/api/payment/verify/<reference>`
6. System verifies payment with Paystack API
7. Updates Purchase.payment_status = 'success'
8. Adds book to library (LibraryItem)
9. Redirects to reading page

## Migration

Run the migration script to add the LibraryItem table:

```bash
python migrate_library.py
```

## Key Features

1. **Separation of Concerns**:
   - Discovery (Search/Home)
   - Preview (Book details + sample)
   - Library (User's collection)
   - Reading (Full access)

2. **Access Control**:
   - Preview: Everyone
   - Add to Library: Logged in users
   - Favorites: Only for owned books
   - Full Reading: Free or purchased books only

3. **Payment Integration**:
   - Proper Paystack initialization
   - Callback URL handling
   - Error handling and retries
   - Automatic library addition on success

4. **User Experience**:
   - Clear visual hierarchy
   - Intuitive navigation
   - Responsive design
   - Touch-friendly carousel

## Troubleshooting

### Payment Fails
1. Check Paystack API keys in `.env`
2. Verify callback URL is accessible
3. Check network connectivity
4. Review Paystack dashboard for errors

### Books Not Showing in Library
1. Verify LibraryItem record exists
2. Check filter selection
3. For "Your Books": Verify purchase status or is_free flag

### Cannot Access Reading Page
1. Check if book is in library (LibraryItem)
2. Verify purchase status for paid books
3. Check user authentication

## Configuration

Ensure `.env` contains:
```
PAYSTACK_PUBLIC_KEY=pk_test_...
PAYSTACK_SECRET_KEY=sk_test_...
```

## Preview Content Configuration

To change the number of preview pages, edit `routes.py`:

```python
@app.route('/preview/<book_id>')
def preview(book_id):
    preview_count = 3  # Change this number (3-5 recommended)
    ...
```
