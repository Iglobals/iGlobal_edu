from flask import render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from functools import wraps
from app import app, db
from models import User, Book, Review, Purchase
from datetime import datetime
import re
import io

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You need admin privileges to access this page.', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    total_books = Book.query.count()
    total_users = User.query.filter_by(is_admin=False).count()
    total_purchases = Purchase.query.filter_by(payment_status='success').count()
    total_reviews = Review.query.count()
    
    recent_purchases = Purchase.query.filter_by(payment_status='success').order_by(Purchase.created_at.desc()).limit(10).all()
    recent_reviews = Review.query.order_by(Review.created_at.desc()).limit(10).all()
    
    # Calculate revenue
    total_revenue = db.session.query(db.func.sum(Purchase.amount_paid)).filter_by(payment_status='success').scalar() or 0
    
    return render_template('admin/dashboard.html',
                         total_books=total_books,
                         total_users=total_users,
                         total_purchases=total_purchases,
                         total_reviews=total_reviews,
                         total_revenue=total_revenue,
                         recent_purchases=recent_purchases,
                         recent_reviews=recent_reviews)

@app.route('/admin/books')
@login_required
@admin_required
def admin_books():
    books = Book.query.order_by(Book.created_at.desc()).all()
    return render_template('admin/books.html', books=books)

@app.route('/admin/books/create', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_create_book():
    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        category = request.form.get('category')
        description = request.form.get('description')
        image_url = request.form.get('image_url')
        price_naira = float(request.form.get('price_naira', 0))
        is_free = request.form.get('is_free') == 'on'
        
        # Process content
        content_type = request.form.get('content_type')
        
        if content_type == 'chapters':
            # Get chapters and content arrays
            chapter_titles = request.form.getlist('chapter_titles[]')
            chapter_contents = request.form.getlist('chapter_contents[]')
            
            chapters = [title.strip() for title in chapter_titles if title.strip()]
            content = [content.strip() for content in chapter_contents if content.strip()]
        else:
            # Whole content - try to split by chapters automatically
            whole_content = request.form.get('whole_content', '')
            chapters, content = process_whole_content(whole_content)
        
        book = Book(
            title=title,
            author=author,
            category=category,
            description=description,
            image_url=image_url,
            price_naira=price_naira,
            is_free=is_free,
            chapters=chapters,
            content=content
        )
        
        db.session.add(book)
        db.session.commit()
        
        flash(f'Book "{title}" created successfully!', 'success')
        return redirect(url_for('admin_books'))
    
    return render_template('admin/create_book.html')

@app.route('/admin/books/<int:book_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_book(book_id):
    book = Book.query.get_or_404(book_id)
    
    if request.method == 'POST':
        book.title = request.form.get('title')
        book.author = request.form.get('author')
        book.category = request.form.get('category')
        book.description = request.form.get('description')
        book.image_url = request.form.get('image_url')
        book.price_naira = float(request.form.get('price_naira', 0))
        book.is_free = request.form.get('is_free') == 'on'
        
        # Update chapters and content
        chapter_titles = request.form.getlist('chapter_titles[]')
        chapter_contents = request.form.getlist('chapter_contents[]')
        
        book.chapters = [title.strip() for title in chapter_titles if title.strip()]
        book.content = [content.strip() for content in chapter_contents if content.strip()]
        
        db.session.commit()
        
        flash(f'Book "{book.title}" updated successfully!', 'success')
        return redirect(url_for('admin_books'))
    
    return render_template('admin/edit_book.html', book=book)

@app.route('/admin/books/<int:book_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_book(book_id):
    book = Book.query.get_or_404(book_id)
    title = book.title
    
    db.session.delete(book)
    db.session.commit()
    
    flash(f'Book "{title}" deleted successfully!', 'success')
    return redirect(url_for('admin_books'))

@app.route('/admin/books/<int:book_id>/purchases')
@login_required
@admin_required
def admin_book_purchases(book_id):
    book = Book.query.get_or_404(book_id)
    purchases = Purchase.query.filter_by(book_id=book_id, payment_status='success').order_by(Purchase.created_at.desc()).all()
    
    total_revenue = sum(p.amount_paid for p in purchases)
    
    return render_template('admin/book_purchases.html', book=book, purchases=purchases, total_revenue=total_revenue)

@app.route('/admin/reviews')
@login_required
@admin_required
def admin_reviews():
    reviews = Review.query.order_by(Review.created_at.desc()).all()
    return render_template('admin/reviews.html', reviews=reviews)

@app.route('/admin/reviews/<int:review_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_review(review_id):
    review = Review.query.get_or_404(review_id)
    
    db.session.delete(review)
    db.session.commit()
    
    flash('Review deleted successfully!', 'success')
    return redirect(url_for('admin_reviews'))

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.filter_by(is_admin=False).order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/users/<int:user_id>')
@login_required
@admin_required
def admin_user_detail(user_id):
    user = User.query.get_or_404(user_id)
    purchases = Purchase.query.filter_by(user_id=user_id, payment_status='success').all()
    reviews = Review.query.filter_by(user_id=user_id).all()
    
    total_spent = sum(p.amount_paid for p in purchases)
    
    return render_template('admin/user_detail.html', user=user, purchases=purchases, reviews=reviews, total_spent=total_spent)

def process_whole_content(content):
    """
    Process whole content and try to split into chapters automatically.
    Looks for patterns like:
    - Chapter 1: Title
    - Chapter 1 - Title
    - CHAPTER 1: TITLE
    - 1. Title
    """
    # Try to find chapter markers
    chapter_pattern = r'(?:Chapter|CHAPTER|Ch\.?)\s*(\d+)[\s:.-]+([^\n]+)'
    matches = list(re.finditer(chapter_pattern, content, re.IGNORECASE))
    
    if matches:
        chapters = []
        contents = []
        
        for i, match in enumerate(matches):
            chapter_num = match.group(1)
            chapter_title = match.group(2).strip()
            chapters.append(f"Chapter {chapter_num}: {chapter_title}")
            
            # Get content from this chapter to the next (or end)
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            chapter_content = content[start:end].strip()
            
            # Wrap in basic HTML if not already
            if not chapter_content.startswith('<'):
                chapter_content = f'<h2 class="text-2xl font-bold text-[#6B2D5C] mb-6 font-condensed">{chapters[-1]}</h2><p class="mb-4">{chapter_content}</p>'
            
            contents.append(chapter_content)
        
        return chapters, contents
    else:
        # No chapters found, treat as single chapter
        chapters = ['Full Content']
        if not content.startswith('<'):
            content = f'<div class="mb-4">{content}</div>'
        contents = [content]
        return chapters, contents

@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_settings():
    if request.method == 'POST':
        # Handle settings update
        flash('Settings updated successfully!', 'success')
        return redirect(url_for('admin_settings'))
    
    return render_template('admin/settings.html')


@app.route('/admin/books/parse-docx', methods=['POST'])
@login_required
@admin_required
def admin_parse_docx():
    """
    Accepts a .docx upload, converts to HTML with mammoth,
    splits on <h1> tags — each H1 = chapter title, content between = chapter body.
    Returns JSON: { chapters: [...], contents: [...], warnings: [...] }
    """
    try:
        import mammoth
        from bs4 import BeautifulSoup
    except ImportError:
        return jsonify({'error': 'mammoth or beautifulsoup4 not installed.'}), 500

    f = request.files.get('docx_file')
    if not f or not f.filename.lower().endswith('.docx'):
        return jsonify({'error': 'Please upload a valid .docx file.'}), 400

    style_map = """
        p[style-name='Heading 1'] => h1:fresh
        p[style-name='Heading 2'] => h2:fresh
        p[style-name='Heading 3'] => h3:fresh
        p[style-name='Heading 4'] => h4:fresh
        r[style-name='Strong']    => strong
        r[style-name='Emphasis']  => em
    """

    result = mammoth.convert_to_html(io.BytesIO(f.read()), style_map=style_map)
    soup = BeautifulSoup(result.value, 'html.parser')

    chapters, contents = [], []
    current_title, current_nodes = None, []

    for tag in soup.children:
        if getattr(tag, 'name', None) == 'h1':
            if current_title is not None:
                chapters.append(current_title)
                contents.append(''.join(str(n) for n in current_nodes))
            current_title = tag.get_text(strip=True)
            current_nodes = []
        else:
            if str(tag).strip():
                current_nodes.append(tag)

    # flush last chapter
    if current_title is not None:
        chapters.append(current_title)
        contents.append(''.join(str(n) for n in current_nodes))
    elif current_nodes:
        chapters.append('Full Document')
        contents.append(''.join(str(n) for n in current_nodes))

    return jsonify({
        'chapters': chapters,
        'contents': contents,
        'warnings': [w.message for w in result.messages]
    })
