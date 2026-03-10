from flask import render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import app
from extensions import db
from models import User, Book, Review, Favorite, Purchase, Note, LibraryItem
import requests
from datetime import datetime

@app.route('/')
def index():
    featured_books = Book.query.limit(3).all()
    return render_template('index.html', featured_books=featured_books)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/search')
def search():
    query = request.args.get('q', '')
    category = request.args.get('category', 'all')
    
    books_query = Book.query
    
    if query:
        books_query = books_query.filter(
            db.or_(
                Book.title.ilike(f'%{query}%'),
                Book.author.ilike(f'%{query}%'),
                Book.category.ilike(f'%{query}%')
            )
        )
    
    if category != 'all':
        books_query = books_query.filter(Book.category.ilike(f'%{category}%'))
    
    books = books_query.all()
    return render_template('search.html', books=books, query=query, category=category)

@app.route('/preview/<int:book_id>')
def preview(book_id):
    book = Book.query.get_or_404(book_id)
    
    # Get preview content (first 3-5 pages)
    preview_count = 3  # Can be changed easily
    preview_chapters = book.chapters[:preview_count] if book.chapters else []
    preview_content = book.content[:preview_count] if book.content else []
    
    # Check if in library (if logged in)
    in_library = False
    if current_user.is_authenticated:
        in_library = LibraryItem.query.filter_by(user_id=current_user.id, book_id=book_id).first() is not None
    
    return render_template('preview.html', 
                         book=book, 
                         preview_chapters=preview_chapters,
                         preview_content=preview_content,
                         in_library=in_library)

@app.route('/library')
@login_required
def library():
    filter_type = request.args.get('filter', 'added')
    
    if filter_type == 'your_books':
        # Books that are free OR purchased successfully
        library_items = LibraryItem.query.filter_by(user_id=current_user.id).all()
        book_ids = [item.book_id for item in library_items]
        purchased_ids = [p.book_id for p in Purchase.query.filter_by(user_id=current_user.id, payment_status='success').all()]
        
        # Get books that are either free or purchased
        books = Book.query.filter(
            Book.id.in_(book_ids),
            db.or_(Book.is_free == True, Book.id.in_(purchased_ids))
        ).all()
        
    elif filter_type == 'favorites':
        # Favorites (subset of your_books)
        favorites = Favorite.query.filter_by(user_id=current_user.id).all()
        fav_book_ids = [fav.book_id for fav in favorites]
        
        # Only show favorites that user has access to
        library_items = LibraryItem.query.filter_by(user_id=current_user.id).all()
        library_book_ids = [item.book_id for item in library_items]
        purchased_ids = [p.book_id for p in Purchase.query.filter_by(user_id=current_user.id, payment_status='success').all()]
        
        books = Book.query.filter(
            Book.id.in_(fav_book_ids),
            Book.id.in_(library_book_ids),
            db.or_(Book.is_free == True, Book.id.in_(purchased_ids))
        ).all()
        
    else:  # 'added' - default
        # All books added to library (free or paid, purchased or not)
        library_items = LibraryItem.query.filter_by(user_id=current_user.id).all()
        books = [item.book for item in library_items]
    
    # Check purchase status for each book
    purchased_ids = [p.book_id for p in Purchase.query.filter_by(user_id=current_user.id, payment_status='success').all()]
    for book in books:
        book.is_purchased = book.id in purchased_ids or book.is_free
    
    return render_template('library.html', books=books, filter_type=filter_type)

@app.route('/reading/<int:book_id>')
@login_required
def reading(book_id):
    book = Book.query.get_or_404(book_id)
    
    # Check if book is in library
    library_item = LibraryItem.query.filter_by(user_id=current_user.id, book_id=book_id).first()
    if not library_item:
        flash('Please add this book to your library first.', 'warning')
        return redirect(url_for('preview', book_id=book_id))
    
    # Check if user has access (free or purchased)
    if not book.is_free:
        purchase = Purchase.query.filter_by(user_id=current_user.id, book_id=book_id, payment_status='success').first()
        if not purchase:
            flash('You need to purchase this book to read it.', 'warning')
            return redirect(url_for('library', filter='added'))
    
    page = request.args.get('page', 1, type=int)
    reviews = Review.query.filter_by(book_id=book_id).order_by(Review.created_at.desc()).all()
    notes = Note.query.filter_by(user_id=current_user.id, book_id=book_id).all()
    
    return render_template('reading.html', book=book, page=page, reviews=reviews, notes=notes)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('library'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('library'))
        else:
            flash('Invalid email or password', 'danger')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('library'))
    
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('signup'))
        
        user = User(
            full_name=full_name,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        flash('Account created successfully!', 'success')
        return redirect(url_for('library'))
    
    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/forgot-password')
def forgot_password():
    return render_template('forgot_password.html')

# API Routes
@app.route('/api/library/add/<int:book_id>', methods=['POST'])
@login_required
def add_to_library(book_id):
    book = Book.query.get_or_404(book_id)
    library_item = LibraryItem.query.filter_by(user_id=current_user.id, book_id=book_id).first()
    
    if library_item:
        return jsonify({'status': 'already_added', 'message': 'Book already in library'})
    
    library_item = LibraryItem(user_id=current_user.id, book_id=book_id)
    db.session.add(library_item)
    db.session.commit()
    
    return jsonify({'status': 'added', 'message': 'Added to library'})

@app.route('/api/library/remove/<int:book_id>', methods=['POST'])
@login_required
def remove_from_library(book_id):
    library_item = LibraryItem.query.filter_by(user_id=current_user.id, book_id=book_id).first()

    if not library_item:
        return jsonify({'status': 'error', 'message': 'Book not in library'}), 404

    # Check if purchased (if not free)
    book = Book.query.get(book_id)
    if not book.is_free:
        purchase = Purchase.query.filter_by(user_id=current_user.id, book_id=book_id, payment_status='success').first()
        if purchase:
            return jsonify({'status': 'error', 'message': 'Cannot remove a purchased book from library'}), 400

    db.session.delete(library_item)
    db.session.commit()

    return jsonify({'status': 'removed', 'message': 'Removed from library'})

@app.route('/api/favorite/<int:book_id>', methods=['POST'])
@login_required
def toggle_favorite(book_id):
    book = Book.query.get_or_404(book_id)
    
    # Check if book is in library and accessible
    library_item = LibraryItem.query.filter_by(user_id=current_user.id, book_id=book_id).first()
    if not library_item:
        return jsonify({'status': 'error', 'message': 'Book must be in your library first'}), 400
    
    # Check if user has access (free or purchased)
    if not book.is_free:
        purchase = Purchase.query.filter_by(user_id=current_user.id, book_id=book_id, payment_status='success').first()
        if not purchase:
            return jsonify({'status': 'error', 'message': 'You must purchase this book first'}), 400
    
    favorite = Favorite.query.filter_by(user_id=current_user.id, book_id=book_id).first()
    
    if favorite:
        db.session.delete(favorite)
        db.session.commit()
        return jsonify({'status': 'removed', 'message': 'Removed from favorites'})
    else:
        favorite = Favorite(user_id=current_user.id, book_id=book_id)
        db.session.add(favorite)
        db.session.commit()
        return jsonify({'status': 'added', 'message': 'Added to favorites'})

@app.route('/api/review/<int:book_id>', methods=['POST'])
@login_required
def add_review(book_id):
    book = Book.query.get_or_404(book_id)
    data = request.get_json()
    
    rating = data.get('rating')
    comment = data.get('comment', '')
    
    if not rating or rating < 1 or rating > 5:
        return jsonify({'error': 'Invalid rating'}), 400
    
    review = Review(
        user_id=current_user.id,
        book_id=book_id,
        rating=rating,
        comment=comment
    )
    db.session.add(review)
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'review': {
            'id': review.id,
            'user_name': current_user.full_name,
            'rating': review.rating,
            'comment': review.comment,
            'created_at': review.created_at.strftime('%Y-%m-%d')
        }
    })

@app.route('/api/review/<int:review_id>/like', methods=['POST'])
@login_required
def like_review(review_id):
    review = Review.query.get_or_404(review_id)
    review.likes += 1
    db.session.commit()
    return jsonify({'status': 'success', 'likes': review.likes})

@app.route('/api/review/<int:review_id>/dislike', methods=['POST'])
@login_required
def dislike_review(review_id):
    review = Review.query.get_or_404(review_id)
    review.dislikes += 1
    db.session.commit()
    return jsonify({'status': 'success', 'dislikes': review.dislikes})

@app.route('/api/note/<int:book_id>', methods=['POST'])
@login_required
def add_note(book_id):
    book = Book.query.get_or_404(book_id)
    data = request.get_json()
    
    note = Note(
        user_id=current_user.id,
        book_id=book_id,
        chapter_number=data.get('chapter', 1),
        content=data.get('content', '')
    )
    db.session.add(note)
    db.session.commit()
    
    return jsonify({'status': 'success', 'note_id': note.id})

@app.route('/payment/<int:book_id>')
@login_required
def payment(book_id):
    book = Book.query.get_or_404(book_id)
    
    if book.is_free:
        flash('This book is free!', 'info')
        return redirect(url_for('reading', book_id=book_id))
    
    # Check if already purchased
    purchase = Purchase.query.filter_by(user_id=current_user.id, book_id=book_id, payment_status='success').first()
    if purchase:
        return redirect(url_for('reading', book_id=book_id))
    
    # Calculate total with charges for display
    total_amount = calculate_paystack_total(book.price_naira)

    return render_template('payment.html',
                         book=book,
                         total_amount=total_amount,
                         paystack_public_key=app.config['PAYSTACK_PUBLIC_KEY'])

def calculate_paystack_total(amount):
    """
    Calculate the total amount to charge the user so that the merchant receives 'amount'.
    Paystack Fee: 1.5% + NGN 100
    NGN 100 fee is waived for transactions below NGN 2,500.
    Fee is capped at NGN 2,000.
    """
    if amount < 2500:
        total = (amount) / (1 - 0.015)
    else:
        total = (amount + 100) / (1 - 0.015)

    # Check if fee exceeds 2000
    if total - amount > 2000:
        total = amount + 2000

    return round(total, 2)

@app.route('/api/payment/initialize', methods=['POST'])
@login_required
def initialize_payment():
    try:
        data = request.get_json()
        book_id = data.get('book_id')
        book = Book.query.get_or_404(book_id)

        # Calculate total with charges
        total_to_charge = calculate_paystack_total(book.price_naira)

        # Check if already purchased
        existing_purchase = Purchase.query.filter_by(
            user_id=current_user.id,
            book_id=book_id,
            payment_status='success'
        ).first()

        if existing_purchase:
            return jsonify({'status': 'error', 'message': 'Book already purchased'}), 400

        # Create or update purchase record
        purchase = Purchase.query.filter_by(
            user_id=current_user.id,
            book_id=book_id
        ).filter(Purchase.payment_status != 'success').first()

        if not purchase:
            purchase = Purchase(
                user_id=current_user.id,
                book_id=book_id,
                amount_paid=total_to_charge,
                payment_status='pending'
            )
            db.session.add(purchase)
            db.session.flush()  # Get the ID without committing
        else:
            purchase.amount_paid = total_to_charge

        # Generate unique reference
        reference = f'IGS-{purchase.id}-{int(datetime.now().timestamp())}'
        purchase.payment_reference = reference
        db.session.commit()

        # Initialize Paystack payment
        url = 'https://api.paystack.co/transaction/initialize'
        headers = {
            'Authorization': f'Bearer {app.config["PAYSTACK_SECRET_KEY"]}',
            'Content-Type': 'application/json'
        }
        payload = {
            'email': current_user.email,
            'amount': int(total_to_charge * 100),  # Paystack uses kobo
            'reference': reference,
            'callback_url': url_for('verify_payment', reference=reference, _external=True),
            'metadata': {
                'purchase_id': purchase.id,
                'book_id': book_id,
                'book_title': book.title,
                'user_id': current_user.id,
                'user_name': current_user.full_name,
                'base_amount': book.price_naira,
                'total_amount': total_to_charge
            }
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get('status'):
                return jsonify({
                    'status': 'success', 
                    'data': response_data['data'],
                    'reference': reference
                })
        
        # If we get here, something went wrong
        error_message = response.json().get('message', 'Payment initialization failed')
        return jsonify({'status': 'error', 'message': error_message}), 400
        
    except requests.exceptions.RequestException as e:
        return jsonify({'status': 'error', 'message': f'Network error: {str(e)}'}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': f'Server error: {str(e)}'}), 500

@app.route('/api/payment/verify/<reference>')
@login_required
def verify_payment(reference):
    try:
        url = f'https://api.paystack.co/transaction/verify/{reference}'
        headers = {'Authorization': f'Bearer {app.config["PAYSTACK_SECRET_KEY"]}'}
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get('status') and response_data['data']['status'] == 'success':
                purchase = Purchase.query.filter_by(payment_reference=reference).first()
                if purchase:
                    purchase.payment_status = 'success'
                    
                    # Also add to library if not already there
                    library_item = LibraryItem.query.filter_by(
                        user_id=current_user.id,
                        book_id=purchase.book_id
                    ).first()
                    
                    if not library_item:
                        library_item = LibraryItem(
                            user_id=current_user.id,
                            book_id=purchase.book_id
                        )
                        db.session.add(library_item)
                    
                    db.session.commit()
                    
                    flash('Payment successful! You can now access the book.', 'success')
                    return redirect(url_for('reading', book_id=purchase.book_id))
        
        flash('Payment verification failed. Please contact support.', 'danger')
        return redirect(url_for('library', filter='added'))
        
    except Exception as e:
        flash(f'Error verifying payment: {str(e)}', 'danger')
        return redirect(url_for('library', filter='added'))

@app.context_processor
def inject_user():
    return dict(current_user=current_user)
