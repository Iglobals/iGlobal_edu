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

@app.route('/admin/books/<int:book_id>/view')
@login_required
@admin_required
def admin_book_view(book_id):
    book = Book.query.get_or_404(book_id)
    return render_template('admin/bookview.html', book=book)


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


def _fix_interrupted_lists(soup):
    """
    Mammoth splits interrupted numbered lists into multiple <ol> blocks,
    each restarting at 1. This function finds ALL <ol> elements anywhere
    in the document (not just top-level) and sets the correct `start`
    attribute so numbering is continuous across interruptions.
    """
    from bs4 import NavigableString, Tag

    def fix_in_parent(parent):
        children = [c for c in parent.children if isinstance(c, Tag)]
        running = 0
        last_ol = None

        for child in children:
            if child.name == 'ol':
                if running > 0:
                    # This ol continues a previous one — set start
                    child['start'] = running + 1
                running += len(child.find_all('li', recursive=False))
                last_ol = child
            elif child.name in ('h1','h2','h3','h4','p','blockquote','div'):
                # Interrupting content — keep running count alive
                # Recurse into divs in case lists are nested inside them
                if child.name == 'div':
                    fix_in_parent(child)
            else:
                # Something else resets the list context
                running = 0
                last_ol = None

    fix_in_parent(soup)


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
        return jsonify({'error': 'Server is missing required libraries (mammoth / beautifulsoup4). Ask your developer to run: pip install mammoth beautifulsoup4'}), 500

    f = request.files.get('docx_file')
    if not f:
        return jsonify({'error': 'No file was received. Please choose a .docx file and try again.'}), 400
    if not f.filename.lower().endswith('.docx'):
        return jsonify({'error': f'"{f.filename}" is not a Word document. Only .docx files are supported (not .doc, .pdf, or .odt).'}), 400

    style_map = """
        p[style-name='Heading 1'] => h1:fresh
        p[style-name='Heading 2'] => h2:fresh
        p[style-name='Heading 3'] => h3:fresh
        p[style-name='Heading 4'] => h4:fresh
        r[style-name='Strong']    => strong
        r[style-name='Emphasis']  => em
    """

    import base64

    def convert_image(image):
        try:
            with image.open() as img_bytes:
                encoded = base64.b64encode(img_bytes.read()).decode('ascii')
            return {'src': f'data:{image.content_type};base64,{encoded}'}
        except Exception:
            return {}  # skip unreadable images silently

    try:
        file_bytes = f.read()
        if len(file_bytes) == 0:
            return jsonify({'error': 'The uploaded file is empty. Please check the file and try again.'}), 400

        result = mammoth.convert_to_html(
            io.BytesIO(file_bytes),
            style_map=style_map,
            convert_image=mammoth.images.img_element(convert_image)
        )
    except Exception as e:
        err = str(e).lower()
        if 'zip' in err or 'bad magic' in err or 'not a zip' in err:
            return jsonify({'error': 'The file appears to be corrupted or is not a valid .docx file. Try re-saving it in Word as "Word Document (.docx)" and upload again.'}), 400
        if 'password' in err or 'encrypted' in err:
            return jsonify({'error': 'This document is password-protected. Remove the password in Word (File → Info → Protect Document) and try again.'}), 400
        return jsonify({'error': f'Could not read the document: {str(e)}'}), 500

    try:
        soup = BeautifulSoup(result.value, 'html.parser')

        # ── Strip inline styles from headings (CSS handles colors) ──
        for tag_name in ['h1', 'h2', 'h3', 'h4']:
            for tag in soup.find_all(tag_name):
                if 'style' in tag.attrs:
                    del tag.attrs['style']

        # ── Fix interrupted numbered lists ──────────────────────────
        _fix_interrupted_lists(soup)

        # ── Style tables ─────────────────────────────────────────────
        for table in soup.find_all('table'):
            wrapper = soup.new_tag('div', style='overflow-x:auto;margin:1em 0;')
            table.insert_before(wrapper)
            table.extract()
            wrapper.append(table)

            table['style'] = (
                'width:100%;border-collapse:collapse;'
                'font-size:0.9em;font-family:Georgia,serif;min-width:400px;'
            )
            rows = table.find_all('tr')
            for i, tr in enumerate(rows):
                bg = '#f3e8ff' if i == 0 else ('#faf5ff' if i % 2 == 0 else 'white')
                tr['style'] = f'background:{bg};'
                for cell in tr.find_all(['td', 'th']):
                    base = 'padding:0.45rem 0.75rem;border:1px solid #e5e7eb;vertical-align:top;text-align:left;'
                    if cell.name == 'th' or i == 0:
                        cell['style'] = base + 'font-weight:700;color:#2F1341;background:#f3e8ff;'
                    else:
                        cell['style'] = base

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

        if current_title is not None:
            chapters.append(current_title)
            contents.append(''.join(str(n) for n in current_nodes))
        elif current_nodes:
            chapters.append('Full Document')
            contents.append(''.join(str(n) for n in current_nodes))

        if not chapters:
            return jsonify({'error': 'No content was found in the document. Make sure the file has text and is not blank.'}), 400

        # Filter mammoth warnings — skip the tr/td/th ones we know are harmless
        warnings = [
            w.message for w in result.messages
            if not any(x in w.message for x in ['tr =>', 'td =>', 'th =>'])
        ]

        return jsonify({
            'chapters': chapters,
            'contents': contents,
            'warnings': warnings
        })

    except Exception as e:
        return jsonify({'error': f'Document was read but could not be processed: {str(e)}'}), 500
