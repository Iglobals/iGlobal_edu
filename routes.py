from flask import render_template, request, redirect, url_for, flash, jsonify, make_response, session
from flask_login import login_required, current_user
from app import app
from extensions import db
from models import User, Book, Review, Favorite, Purchase, Note, LibraryItem
import mongo_books
import exam_packages
from exam_packages import PACKAGE_BOOK, PACKAGES
import itest_client
import payments
import requests
import os
import time
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
        Book.image_url, Book.price_naira, Book.is_free, Book.chapters,
        Book.exam_keys, Book.exam_addon_price_naira
    ).filter(Book.id == book_id).first_or_404()

    # Public, cacheable info only (no per-user state) - see Cache-Control below.
    exam_offer = None
    if exam_packages.offers_exam_package(book):
        exam_offer = {
            'addon': book.exam_addon_price_naira,
            'package_price': (book.price_naira or 0) + book.exam_addon_price_naira,
            'labels': exam_packages.exam_labels(book.exam_keys),
        }

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
                         in_library=in_library,
                         exam_offer=exam_offer))
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

    # Opportunistic retry of this user's exam grants iTest hasn't confirmed
    # yet - bounded (2 records, short timeout) and throttled to once per 5
    # minutes per session so a down iTest can't keep the library page slow.
    now = int(time.time())
    if itest_client.is_configured() and now - session.get('exam_grant_retry_at', 0) > 300:
        session['exam_grant_retry_at'] = now
        try:
            payments.retry_pending_exam_grants(user_id=current_user.id, limit=2, timeout=4)
        except Exception as exc:  # never break the library page over this
            db.session.rollback()
            app.logger.warning('exam grant retry failed: %s', exc)

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

    # Build book list with is_purchased flag.
    book_list = []
    for b in books:
        d = b._asdict() if hasattr(b, '_asdict') else dict(b)
        d['is_purchased'] = b.id in purchased_ids or b.is_free
        book_list.append(d)

    return render_template('library.html', books=book_list, filter_type=filter_type,
                           itest_exams_url=itest_client.my_exams_url())


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

    offers_exam = exam_packages.offers_exam_package(book)
    purchase = Purchase.query.filter_by(user_id=current_user.id, book_id=book_id, payment_status='success').first()
    mode = 'new'
    if purchase:
        source, _ = get_exam_access(current_user.id, book_id)
        if not offers_exam or source is not None:
            return redirect(url_for('reading', book_id=book_id))
        mode = 'upgrade'   # owns the book-only version: offer just the exam add-on

    selected = request.args.get('package', PACKAGE_BOOK)
    resp = make_response(render_template(
        'payment.html', book=book, paystack_public_key=app.config['PAYSTACK_PUBLIC_KEY'],
        mode=mode, offers_exam=offers_exam,
        selected_package=selected if selected in PACKAGES else PACKAGE_BOOK,
        package_price=exam_packages.package_price_naira(book, PACKAGE_BOOK_EXAM) if offers_exam else None,
        exam_labels=exam_packages.exam_labels(book.exam_keys) if offers_exam else [],
    ))

    # Set referral cookie if ?ref= is in the URL and no cookie already set
    ref = request.args.get('ref', '').strip()
    if ref and not request.cookies.get('igref'):
        from models import REFERRAL_COOKIE_DAYS
        resp.set_cookie('igref', ref, max_age=REFERRAL_COOKIE_DAYS * 86400, httponly=True, samesite='Lax')

    return resp

def _paystack_initialize(*, email, amount_kobo, reference, metadata):
    url = 'https://api.paystack.co/transaction/initialize'
    headers = {
        'Authorization': f'Bearer {app.config["PAYSTACK_SECRET_KEY"]}',
        'Content-Type': 'application/json'
    }
    payload = {
        'email': email,
        'amount': amount_kobo,  # Paystack uses kobo
        'reference': reference,
        'callback_url': url_for('verify_payment', reference=reference, _external=True),
        'metadata': {
            **metadata,
            # Required for ICA's centralized webhook relay to route this
            # event back to this app, and to this specific handler within
            # it (see ica_webhook_routes.py / docs/PAYSTACK_WEBHOOK_RELAY.md).
            'client_id': app.config.get('ICA_CLIENT_ID', ''),
        }
    }
    return requests.post(url, json=payload, headers=headers, timeout=10)


@app.route('/api/payment/initialize', methods=['POST'])
@login_required
def initialize_payment():
    """Body: {"book_id": int, "package": "book" | "book_exam"}. The amount is
    ALWAYS computed here from the book's live prices - any amount the client
    sends is ignored. If the user already owns the book as 'book' and asks
    for 'book_exam', this becomes an exam-access upgrade for just the add-on."""
    try:
        data = request.get_json(silent=True) or {}
        package = data.get('package') or PACKAGE_BOOK
        if package not in PACKAGES:
            return jsonify({'status': 'error', 'message': 'Invalid package'}), 400
        book = db.session.get(Book, data.get('book_id')) if str(data.get('book_id', '')).isdigit() else None
        if book is None:
            return jsonify({'status': 'error', 'message': 'Book not found'}), 404
        book_id = book.id
        if book.is_free:
            return jsonify({'status': 'error', 'message': 'This book is free'}), 400
        if package == PACKAGE_BOOK_EXAM and not exam_packages.offers_exam_package(book):
            return jsonify({'status': 'error', 'message': 'Exam access is not offered for this book'}), 400

        existing_purchase = Purchase.query.filter_by(
            user_id=current_user.id,
            book_id=book_id,
            payment_status='success'
        ).first()

        ts = int(datetime.now().timestamp())
        if existing_purchase:
            source, _ = get_exam_access(current_user.id, book_id)
            if package != PACKAGE_BOOK_EXAM or source is not None:
                return jsonify({'status': 'error', 'message': 'Book already purchased'}), 400

            # ── Upgrade: book-only owner buys exam access for the add-on price ──
            amount_naira = exam_packages.upgrade_price_naira(book)
            upgrade = ExamAccessPurchase.query.filter_by(user_id=current_user.id, book_id=book_id).first()
            if not upgrade:
                upgrade = ExamAccessPurchase(user_id=current_user.id, book_id=book_id,
                                             amount_paid=amount_naira, payment_status='pending')
                db.session.add(upgrade)
                db.session.flush()
            upgrade.amount_paid = amount_naira   # always live price
            reference = f'IGX-{upgrade.id}-{ts}'
            upgrade.payment_reference = reference
            db.session.commit()
            response_package = 'exam_upgrade'
            metadata = {
                'exam_access_purchase_id': upgrade.id,
                'purpose': 'exam_upgrade',
                'package': 'exam_upgrade',
            }
        else:
            # ── New purchase: book only, or book + exam package ──
            amount_naira = exam_packages.package_price_naira(book, package)
            purchase = Purchase.query.filter_by(
                user_id=current_user.id,
                book_id=book_id
            ).filter(Purchase.payment_status != 'success').first()

            if not purchase:
                purchase = Purchase(
                    user_id=current_user.id,
                    book_id=book_id,
                    amount_paid=amount_naira,
                    package=package,
                    payment_status='pending'
                )
                db.session.add(purchase)
                db.session.flush()
            # Re-price in case the price or the chosen package changed since
            # the pending record was created
            purchase.amount_paid = amount_naira
            purchase.package = package

            reference = f'IGS-{purchase.id}-{ts}'
            purchase.payment_reference = reference
            db.session.commit()
            response_package = package
            metadata = {
                'purchase_id': purchase.id,
                'purpose': 'book_purchase',
                'package': package,
                'ref_code': request.cookies.get('igref', ''),
            }

        amount_kobo = exam_packages.naira_to_kobo(amount_naira)
        metadata.update({
            'book_id': book_id,
            'book_title': book.title,
            'user_id': current_user.id,
            'user_name': current_user.full_name,
            'exam_keys': list(book.exam_keys or []) if package == PACKAGE_BOOK_EXAM else [],
        })
        response = _paystack_initialize(email=current_user.email, amount_kobo=amount_kobo,
                                        reference=reference, metadata=metadata)

        if response.status_code == 200:
            response_data = response.json()
            if response_data.get('status'):
                return jsonify({
                    'status': 'success',
                    'data': response_data['data'],
                    'reference': reference,
                    # The Paystack popup must use THIS server-computed amount.
                    'amount_kobo': amount_kobo,
                    'amount_naira': amount_naira,
                    'package': response_package,
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
    """Browser callback after the Paystack popup. Fulfilment itself is
    payments.fulfil_charge - the same idempotent, amount-checked function the
    webhook uses, so callback + webhook can both fire safely."""
    try:
        url = f'https://api.paystack.co/transaction/verify/{reference}'
        headers = {'Authorization': f'Bearer {app.config["PAYSTACK_SECRET_KEY"]}'}

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            response_data = response.json()
            tx = response_data.get('data') or {}
            if response_data.get('status') and tx.get('status') == 'success':
                result = payments.fulfil_charge(tx, ref_code=request.cookies.get('igref'))
                if result.ok:
                    record = result.record
                    if result.includes_exam:
                        if record.exam_access_granted_at:
                            flash('Payment successful! Your JUPEB exam access has been granted on iTest. '
                                  'Log in to iTest with this same email to start.', 'success')
                        else:
                            flash('Payment successful! Your JUPEB exam access on iTest is being set up.', 'success')
                        return redirect(url_for('library', filter='added', exam=record.book_id))
                    flash('Payment successful! You can now access the book.', 'success')
                    return redirect(url_for('reading', book_id=record.book_id))
                if result.status == payments.AMOUNT_TOO_LOW:
                    flash('The amount paid does not match the price of this package. '
                          'Please contact support with your payment reference.', 'danger')
                    return redirect(url_for('library', filter='added'))

        flash('Payment verification failed. Please contact support.', 'danger')
        return redirect(url_for('library', filter='added'))

    except Exception as e:
        db.session.rollback()
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
    """charge.success for a book purchase OR an exam upgrade. Kept under this
    name for the legacy route below and ica_webhook_routes.py; the actual
    idempotent, amount-checked logic is payments.fulfil_charge, shared with
    verify_payment."""
    if not data.get('reference') or data.get('status') != 'success':
        return None
    ref_code = (data.get('metadata') or {}).get('ref_code')
    return payments.fulfil_charge(data, ref_code=ref_code)


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
