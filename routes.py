from flask import render_template, request, redirect, url_for, flash, jsonify, session, make_response
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import app
from extensions import db
from models import User, Book, Review, Favorite, Purchase, Note, LibraryItem, OTPCode
import requests
import random
import os
import secrets
from datetime import datetime, timedelta

@app.route('/')
def index():
    books = db.session.query(
        Book.id, Book.title, Book.author, Book.category,
        Book.description, Book.image_url, Book.price_naira, Book.is_free
    ).limit(3).all()
    return render_template('index.html', featured_books=books)

@app.route('/sw.js')
def sw():
    response = make_response(app.send_static_file('sw.js'))
    response.headers['Content-Type'] = 'application/javascript'
    # Ensure scope is root
    response.headers['Service-Worker-Allowed'] = '/'
    return response

@app.route('/manifest.json')
def manifest():
    return app.send_static_file('manifest.json')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/search')
def search():
    query = request.args.get('q', '')
    category = request.args.get('category', 'all')

    books_query = db.session.query(
        Book.id, Book.title, Book.author, Book.category,
        Book.image_url, Book.price_naira, Book.is_free
    )

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
    # Only fetch metadata + preview_content — never touch full content column
    book = db.session.query(
        Book.id, Book.title, Book.author, Book.category, Book.description,
        Book.image_url, Book.price_naira, Book.is_free,
        Book.chapters, Book.preview_content
    ).filter(Book.id == book_id).first_or_404()

    # preview_content holds first 2 chapters; chapters list gives their titles
    preview_chapters = (book.chapters or [])[:2]
    preview_content  = book.preview_content or []

    # Check if in library (if logged in)
    in_library = False
    if current_user.is_authenticated:
        in_library = LibraryItem.query.filter_by(user_id=current_user.id, book_id=book_id).first() is not None

    resp = make_response(render_template('preview.html',
                         book=book,
                         preview_chapters=preview_chapters,
                         preview_content=preview_content,
                         in_library=in_library))
    # Cache preview for 10 minutes — same content for everyone
    resp.headers['Cache-Control'] = 'public, max-age=600'
    return resp

@app.route('/library')
@login_required
def library():
    filter_type = request.args.get('filter', 'added')

    # Columns needed for book cards — never pull content/chapters
    _book_cols = (
        Book.id, Book.title, Book.author, Book.category,
        Book.image_url, Book.price_naira, Book.is_free
    )

    purchased_ids = {
        p.book_id for p in Purchase.query.filter_by(
            user_id=current_user.id, payment_status='success'
        ).with_entities(Purchase.book_id).all()
    }

    if filter_type == 'your_books':
        library_items = LibraryItem.query.filter_by(user_id=current_user.id).all()
        book_ids = [item.book_id for item in library_items]
        books = db.session.query(*_book_cols).filter(
            Book.id.in_(book_ids),
            db.or_(Book.is_free == True, Book.id.in_(purchased_ids))
        ).all()

    elif filter_type == 'favorites':
        fav_book_ids = [
            f.book_id for f in Favorite.query.filter_by(user_id=current_user.id).all()
        ]
        library_book_ids = [
            i.book_id for i in LibraryItem.query.filter_by(user_id=current_user.id).all()
        ]
        books = db.session.query(*_book_cols).filter(
            Book.id.in_(fav_book_ids),
            Book.id.in_(library_book_ids),
            db.or_(Book.is_free == True, Book.id.in_(purchased_ids))
        ).all()

    else:  # 'added' — default
        library_items = LibraryItem.query.filter_by(user_id=current_user.id).all()
        lib_book_ids  = [item.book_id for item in library_items]
        books = db.session.query(*_book_cols).filter(Book.id.in_(lib_book_ids)).all()

    # Attach is_purchased flag (rows are named tuples, so we build plain dicts)
    book_list = []
    for b in books:
        d = b._asdict() if hasattr(b, '_asdict') else dict(b)
        d['is_purchased'] = b.id in purchased_ids or b.is_free
        book_list.append(d)

    return render_template('library.html', books=book_list, filter_type=filter_type)

@app.route('/reading/<int:book_id>')
@login_required
def reading(book_id):
    # Only fetch metadata — content is loaded on demand via /api/book/<id>/chapter/<n>
    book = db.session.query(
        Book.id, Book.title, Book.author, Book.category,
        Book.is_free, Book.chapters
    ).filter(Book.id == book_id).first_or_404()

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

    resp = make_response(render_template('reading.html', book=book, page=page, reviews=reviews, notes=notes))
    # Private — per-user, but still cacheable in the browser for 5 min
    resp.headers['Cache-Control'] = 'private, max-age=300'
    return resp


@app.route('/api/book/<int:book_id>/chapter/<int:chapter_index>')
@login_required
def get_chapter(book_id, chapter_index):
    """Return a single chapter's HTML. Only accessible to users with read access."""
    book = db.session.query(
        Book.id, Book.is_free, Book.content
    ).filter(Book.id == book_id).first_or_404()

    # Access check
    if not book.is_free:
        purchase = Purchase.query.filter_by(
            user_id=current_user.id, book_id=book_id, payment_status='success'
        ).first()
        if not purchase:
            return jsonify({'error': 'Access denied'}), 403

    content = book.content or []
    if chapter_index < 0 or chapter_index >= len(content):
        return jsonify({'error': 'Chapter not found'}), 404

    resp = jsonify({'html': content[chapter_index], 'total': len(content)})
    resp.headers['Cache-Control'] = 'private, max-age=3600'
    return resp

def _get_client_ip():
    """Get real client IP, respecting reverse-proxy headers."""
    forwarded = request.headers.get('X-Forwarded-For', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.remote_addr or '0.0.0.0'


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('library'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        user = User.query.filter_by(email=email).first()

        if not user:
            flash('No account found with that email address.', 'danger')
        elif not check_password_hash(user.password_hash, password):
            flash('Incorrect password. Please try again.', 'danger')
        else:
            client_ip = _get_client_ip()

            # IP lock check — if a different IP is already locked, block login
            # if user.locked_ip and user.locked_ip != client_ip:
            #     flash(
            #         'This account is locked to another device. '
            #         'Please contact support to unlock your account.',
            #         'danger'
            #     )
            #     return render_template('login.html')

            remember = request.form.get('remember', False)
            # Force remember and permanent session for PWA / Mobile users
            remember = True
            session.permanent = True
            
            # Lock to this IP on first login (or same IP returning)
            # if not user.locked_ip:
            #     user.locked_ip = client_ip
            user.session_token = secrets.token_hex(32)
            db.session.commit()
            login_user(user, remember=remember)
            session['user_session_token'] = user.session_token
            next_page = request.args.get('next')
            return redirect(next_page if next_page else url_for('library'))

    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('library'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not full_name:
            flash('Please enter your full name.', 'danger')
        elif User.query.filter_by(email=email).first():
            flash('An account with that email already exists. Try logging in instead.', 'danger')
        elif len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
        elif password != confirm_password:
            flash('Passwords do not match.', 'danger')
        else:
            user = User(
                full_name=full_name,
                email=email,
                password_hash=generate_password_hash(password)
            )
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash('Account created successfully! Welcome to iGlobals.', 'success')
            return redirect(url_for('library'))

    return render_template('signup.html')

@app.route('/logout')
@login_required
def logout():
    current_user.session_token = None
    db.session.commit()
    logout_user()
    return redirect(url_for('index'))

def send_otp_email(to_email, to_name, otp):
    """Send OTP via Brevo transactional email API."""
    api_key = os.environ.get('BREVO_API_KEY', '')
    payload = {
        "sender": {
            "name": os.environ.get('EMAIL_FROM_NAME', 'iGlobals'),
            "email": os.environ.get('EMAIL_FROM', 'no-reply@iglobals.com')
        },
        "to": [{"email": to_email, "name": to_name}],
        "subject": "Your iGlobals Password Reset OTP",
        "htmlContent": (
            "<html><body style='font-family:Inter,sans-serif;background:#f3f4f6;padding:2rem;'>"
            "<div style='max-width:480px;margin:0 auto;background:white;border-radius:12px;padding:2.5rem;box-shadow:0 4px 20px rgba(0,0,0,0.08);'>"
            "<div style='text-align:center;margin-bottom:1.5rem;'>"
            "<div style='display:inline-block;background:#2F1341;border-radius:8px;padding:0.6rem 1rem;'>"
            "<span style='color:white;font-weight:800;font-size:1.1rem;letter-spacing:0.05em;'>IGLOBALS</span></div></div>"
            "<h2 style='color:#2F1341;font-size:1.4rem;font-weight:700;margin-bottom:0.5rem;'>Password Reset OTP</h2>"
            "<p style='color:#6b7280;margin-bottom:1.5rem;'>Use the code below to reset your password. It expires in <strong>5 minutes</strong>.</p>"
            f"<div style='background:#f3e8ff;border-radius:10px;padding:1.5rem;text-align:center;margin-bottom:1.5rem;'>"
            f"<span style='font-size:2.5rem;font-weight:800;letter-spacing:0.3em;color:#2F1341;'>{otp}</span></div>"
            "<p style='color:#9ca3af;font-size:0.8rem;'>If you didn't request this, you can safely ignore this email.</p>"
            "</div></body></html>"
        )
    }
    headers = {
        'accept': 'application/json',
        'api-key': api_key,
        'content-type': 'application/json'
    }
    try:
        resp = requests.post('https://api.brevo.com/v3/smtp/email', json=payload, headers=headers, timeout=10)
        return resp.status_code == 201
    except Exception:
        return False


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('No account found with that email address.', 'danger')
            return render_template('forgot_password.html')

        # Invalidate any existing unused OTPs for this user
        OTPCode.query.filter_by(user_id=user.id, used=False).delete()
        db.session.flush()

        otp = str(random.randint(100000, 999999))
        record = OTPCode(
            user_id=user.id,
            code=otp,
            expires_at=datetime.utcnow() + timedelta(minutes=5)
        )
        db.session.add(record)
        db.session.commit()

        sent = send_otp_email(email, user.full_name, otp)
        if not sent:
            flash('Failed to send OTP email. Please try again shortly.', 'danger')
            return render_template('forgot_password.html')

        session['otp_user_id'] = user.id
        return redirect(url_for('verify_otp'))
    return render_template('forgot_password.html')


@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    user_id = session.get('otp_user_id')
    if not user_id:
        return redirect(url_for('forgot_password'))

    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        entered = request.form.get('otp', '').strip()
        record = OTPCode.query.filter_by(user_id=user_id, used=False).order_by(OTPCode.created_at.desc()).first()

        if not record or datetime.utcnow() > record.expires_at:
            # Clean up expired record
            if record:
                db.session.delete(record)
                db.session.commit()
            flash('OTP has expired. Please request a new one.', 'danger')
            return redirect(url_for('forgot_password'))

        if entered == record.code:
            record.used = True
            db.session.commit()
            session['otp_verified_user_id'] = user_id
            session.pop('otp_user_id', None)
            return redirect(url_for('reset_password'))
        else:
            flash('Invalid OTP. Please try again.', 'danger')

    return render_template('verify_otp.html', email=user.email)


@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    user_id = session.get('otp_verified_user_id')
    if not user_id:
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm = request.form.get('confirm_password', '')
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return render_template('reset_password.html')
        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('reset_password.html')

        user = User.query.get(user_id)
        if user:
            user.password_hash = generate_password_hash(password)
            db.session.commit()

        session.pop('otp_verified_user_id', None)
        flash('Password reset successfully. You can now log in.', 'success')
        return redirect(url_for('login'))

    return render_template('reset_password.html')

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

    purchase = Purchase.query.filter_by(user_id=current_user.id, book_id=book_id, payment_status='success').first()
    if purchase:
        return redirect(url_for('reading', book_id=book_id))

    resp = make_response(render_template('payment.html', book=book, paystack_public_key=app.config['PAYSTACK_PUBLIC_KEY']))

    # Set referral cookie if ?ref= is in the URL and no cookie already set
    ref = request.args.get('ref', '').strip()
    if ref and not request.cookies.get('igref'):
        from models import REFERRAL_COOKIE_DAYS
        resp.set_cookie('igref', ref, max_age=REFERRAL_COOKIE_DAYS * 86400, httponly=True, samesite='Lax')

    return resp

@app.route('/api/payment/initialize', methods=['POST'])
@login_required
def initialize_payment():
    try:
        data = request.get_json()
        book_id = data.get('book_id')
        book = Book.query.get_or_404(book_id)
        
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
                amount_paid=book.price_naira,   # always live price
                payment_status='pending'
            )
            db.session.add(purchase)
            db.session.flush()
        else:
            # Update amount in case price changed since the pending record was created
            purchase.amount_paid = book.price_naira
        
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
            'amount': int(book.price_naira * 100),  # Paystack uses kobo
            'reference': reference,
            'callback_url': url_for('verify_payment', reference=reference, _external=True),
            'metadata': {
                'purchase_id': purchase.id,
                'book_id': book_id,
                'book_title': book.title,
                'user_id': current_user.id,
                'user_name': current_user.full_name,
                'ref_code': request.cookies.get('igref', '')
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

                    library_item = LibraryItem.query.filter_by(
                        user_id=current_user.id,
                        book_id=purchase.book_id
                    ).first()
                    if not library_item:
                        db.session.add(LibraryItem(
                            user_id=current_user.id,
                            book_id=purchase.book_id
                        ))

                    # Attribute referral commission if cookie present
                    from models import attribute_referral
                    ref_code = request.cookies.get('igref')
                    attribute_referral(purchase, ref_code)

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
    return dict(current_user=current_user, google_enabled=_GOOGLE_ENABLED)


# Endpoints that should never trigger the session check
_AUTH_ENDPOINTS = {'login', 'signup', 'logout', 'forgot_password',
                   'verify_otp', 'reset_password', 'google_login',
                   'google_callback', 'static', 'paystack_webhook'}

@app.before_request
def enforce_single_session():
    """Block requests from IPs that don't match the user's locked IP."""
    if not current_user.is_authenticated:
        return
    if request.endpoint in _AUTH_ENDPOINTS:
        return
    if request.path.startswith('/static/'):
        return
    if current_user.is_admin:
        return  # admins are never IP-locked

    if current_user.locked_ip:
        pass
        # client_ip = _get_client_ip()
        # if client_ip != current_user.locked_ip:
        #     logout_user()
        #     session.clear()
        #     flash(
        #         'Access from a new device was detected. '
        #         'Please contact support to unlock your account.',
        #         'danger'
        #     )
        #     return redirect(url_for('login'))


# ── Paystack Webhook ──────────────────────────────────────────────────────
import hmac
import hashlib

@app.route('/api/payment/webhook', methods=['POST'])
def paystack_webhook():
    secret = os.environ.get('PAYSTACK_SECRET_KEY', '')

    # 1. Verify signature
    sig = request.headers.get('x-paystack-signature', '')
    body = request.get_data()  # raw bytes — must be used before .get_json()
    expected = hmac.new(secret.encode(), body, hashlib.sha512).hexdigest()

    if not hmac.compare_digest(expected, sig):
        return jsonify({'status': 'invalid signature'}), 401

    # 2. Acknowledge immediately (Paystack requires 200 fast)
    event = request.get_json(force=True, silent=True) or {}
    event_type = event.get('event')

    # 3. Handle charge.success
    if event_type == 'charge.success':
        data      = event.get('data', {})
        reference = data.get('reference')
        status    = data.get('status')

        if reference and status == 'success':
            purchase = Purchase.query.filter_by(payment_reference=reference).first()
            if purchase and purchase.payment_status != 'success':
                purchase.payment_status = 'success'

                library_item = LibraryItem.query.filter_by(
                    user_id=purchase.user_id,
                    book_id=purchase.book_id
                ).first()
                if not library_item:
                    db.session.add(LibraryItem(
                        user_id=purchase.user_id,
                        book_id=purchase.book_id
                    ))

                # Attribute referral — webhook carries metadata we stored at init
                from models import attribute_referral
                ref_code = (data.get('metadata') or {}).get('ref_code')
                attribute_referral(purchase, ref_code)

                db.session.commit()

    return jsonify({'status': 'ok'}), 200


# ── Google OAuth ──────────────────────────────────────────────────────────
from authlib.integrations.flask_client import OAuth

_GOOGLE_CLIENT_ID     = os.environ.get('GOOGLE_CLIENT_ID', '')
_GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', '')
_GOOGLE_ENABLED = bool(_GOOGLE_CLIENT_ID and
                       _GOOGLE_CLIENT_ID != 'your-google-client-id-here')

oauth = OAuth(app)
if _GOOGLE_ENABLED:
    google = oauth.register(
        name='google',
        client_id=_GOOGLE_CLIENT_ID,
        client_secret=_GOOGLE_CLIENT_SECRET,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )
else:
    google = None


@app.route('/auth/google')
def google_login():
    if not _GOOGLE_ENABLED:
        flash('Google sign-in is temporarily unavailable. Please use email and password.', 'warning')
        return redirect(url_for('login'))
    redirect_uri = url_for('google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route('/auth/google/callback')
def google_callback():
    if not _GOOGLE_ENABLED:
        return redirect(url_for('login'))
    try:
        token = google.authorize_access_token()
        user_info = token.get('userinfo')
        if not user_info:
            flash('Google authentication failed.', 'danger')
            return redirect(url_for('login'))

        email = user_info.get('email')
        name  = user_info.get('name', email.split('@')[0])

        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(
                full_name=name,
                email=email,
                password_hash=generate_password_hash(secrets.token_hex(16))
            )
            db.session.add(user)
            db.session.commit()

        user.session_token = secrets.token_hex(32)
        db.session.commit()
        login_user(user)
        session['user_session_token'] = user.session_token
        return redirect(url_for('library'))
    except Exception:
        flash('Google sign-in failed. Please try again or use email and password.', 'danger')
        return redirect(url_for('login'))
