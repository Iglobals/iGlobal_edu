from flask import render_template, request, redirect, url_for, flash, jsonify, make_response
from flask_login import login_required, current_user
from app import app
from extensions import db
from models import User, Book, Review, Favorite, Purchase, Note, LibraryItem
import mongo_books
import requests
import os
from datetime import datetime

@app.route('/')
def index():
    books = db.session.query(
        Book.id, Book.title, Book.author, Book.category,
        Book.description, Book.image_url, Book.price_naira, Book.is_free
    ).filter(Book.id.in_([11, 16, 13])).all()
    featured_books = sorted(books, key=lambda x: [11, 16, 13].index(x.id))
    return render_template('index.html', featured_books=featured_books)

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

@app.route('/services')
def services():
    return render_template('services.html')

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
    # Metadata from Postgres; the first 2 chapters' HTML from Mongo (was
    # Book.preview_content - see mongo_books.py for why content moved).
    book = db.session.query(
        Book.id, Book.title, Book.author, Book.category, Book.description,
        Book.image_url, Book.price_naira, Book.is_free, Book.chapters
    ).filter(Book.id == book_id).first_or_404()

    preview_chapters = (book.chapters or [])[:2]
    preview_content = [mongo_books.get_chapter_html(book_id, i) or '' for i in range(len(preview_chapters))]

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
        Book.id, Book.is_free, Book.chapters
    ).filter(Book.id == book_id).first_or_404()

    # Access check
    if not book.is_free:
        purchase = Purchase.query.filter_by(
            user_id=current_user.id, book_id=book_id, payment_status='success'
        ).first()
        if not purchase:
            return jsonify({'error': 'Access denied'}), 403

    total = len(book.chapters or [])
    if chapter_index < 0 or chapter_index >= total:
        return jsonify({'error': 'Chapter not found'}), 404

    html = mongo_books.get_chapter_html(book_id, chapter_index)
    if html is None:
        return jsonify({'error': 'Chapter not found'}), 404

    resp = jsonify({'html': html, 'total': total})
    resp.headers['Cache-Control'] = 'private, max-age=3600'
    return resp

# Login, signup, and password reset are handled by iGlobals Central Auth —
# see auth_routes.py for /auth/login, /auth/callback, and /logout.

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
                'ref_code': request.cookies.get('igref', ''),
                # Required for ICA's centralized webhook relay to route this
                # event back to this app, and to this specific handler within
                # it (see ica_webhook_routes.py / docs/PAYSTACK_WEBHOOK_RELAY.md).
                'client_id': app.config.get('ICA_CLIENT_ID', ''),
                'purpose': 'book_purchase',
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
    return dict(current_user=current_user)


# ── Paystack Webhook ──────────────────────────────────────────────────────
# DEPRECATED as of the ICA centralized webhook relay - Paystack's dashboard
# should point at ICA now, which relays to ica_webhook_routes.py instead of
# here. Left in place (unused once that cutover happens) rather than deleted,
# same rollback-safety reasoning as the Mongo migration. handle_book_charge_success()
# below is the actual logic now, reused by ica_webhook_routes.py - this route
# just calls it too so nothing breaks if Paystack is still pointed here.
import hmac
import hashlib


def handle_book_charge_success(data: dict):
    """The actual book-purchase-webhook logic, extracted so both the legacy
    direct-from-Paystack route below AND the new ICA relay route can call it."""
    reference = data.get('reference')
    status = data.get('status')
    if not reference or status != 'success':
        return

    purchase = Purchase.query.filter_by(payment_reference=reference).first()
    if not purchase or purchase.payment_status == 'success':
        return  # unknown reference, or already processed - idempotent

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

    from models import attribute_referral
    ref_code = (data.get('metadata') or {}).get('ref_code')
    attribute_referral(purchase, ref_code)

    db.session.commit()


@app.route('/api/payment/webhook', methods=['POST'])
def paystack_webhook():
    secret = os.environ.get('PAYSTACK_SECRET_KEY', '')

    sig = request.headers.get('x-paystack-signature', '')
    body = request.get_data()  # raw bytes — must be used before .get_json()
    expected = hmac.new(secret.encode(), body, hashlib.sha512).hexdigest()

    if not hmac.compare_digest(expected, sig):
        return jsonify({'status': 'invalid signature'}), 401

    event = request.get_json(force=True, silent=True) or {}
    if event.get('event') == 'charge.success':
        handle_book_charge_success(event.get('data', {}))

    return jsonify({'status': 'ok'}), 200
