"""
One-time migration script:
  1. Adds preview_content column to books table (if not already present)
  2. Backfills preview_content = first 2 chapters of content for all books
  3. Strips base64-embedded images from content and re-uploads them to Cloudinary

Run once:  python migrate_books.py
"""

import os
import re
import base64
import io
from dotenv import load_dotenv

load_dotenv()

import cloudinary
import cloudinary.uploader

cloudinary.config(
    cloud_name = os.environ['CLOUDINARY_CLOUD_NAME'],
    api_key    = os.environ['CLOUDINARY_API_KEY'],
    api_secret = os.environ['CLOUDINARY_API_SECRET'],
    secure     = True
)

from app import app
from extensions import db
from sqlalchemy import text

# ── 1. Add column if missing ───────────────────────────────────────────────
def ensure_column():
    with db.engine.connect() as conn:
        result = conn.execute(text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name='books' AND column_name='preview_content'"
        ))
        if not result.fetchone():
            conn.execute(text(
                "ALTER TABLE books ADD COLUMN preview_content JSON"
            ))
            conn.commit()
            print("✓ Added preview_content column")
        else:
            print("✓ preview_content column already exists")

# ── 2. Upload a single base64 src to Cloudinary, return secure_url ─────────
def upload_base64_image(data_uri: str) -> str:
    """Extract raw bytes from a data URI and upload to Cloudinary."""
    # data:[mime];base64,[data]
    match = re.match(r'data:([^;]+);base64,(.+)', data_uri, re.DOTALL)
    if not match:
        return data_uri  # not a data URI — leave as-is
    mime, encoded = match.group(1), match.group(2)
    raw = base64.b64decode(encoded)
    result = cloudinary.uploader.upload(
        io.BytesIO(raw),
        folder='iglobals/books',
        resource_type='image'
    )
    return result['secure_url']

# ── 3. Replace all base64 img srcs in an HTML string ──────────────────────
def replace_base64_images(html: str) -> str:
    """Find all data URI img srcs and swap them for Cloudinary URLs."""
    pattern = re.compile(r'src="(data:image/[^"]+)"')
    replaced = 0

    def replacer(m):
        nonlocal replaced
        url = upload_base64_image(m.group(1))
        replaced += 1
        return f'src="{url}"'

    result = pattern.sub(replacer, html)
    if replaced:
        print(f"    ↑ uploaded {replaced} image(s) to Cloudinary")
    return result

# ── 4. Main migration ──────────────────────────────────────────────────────
def migrate():
    from models import Book

    books = Book.query.all()
    print(f"\nMigrating {len(books)} book(s)...\n")

    for book in books:
        print(f"  [{book.id}] {book.title}")
        changed = False

        # Backfill preview_content
        if not book.preview_content and book.content:
            book.preview_content = book.content[:2]
            changed = True
            print("    ✓ preview_content set")

        # Strip base64 images from all chapters
        if book.content:
            new_content = []
            for chapter_html in book.content:
                if 'data:image/' in chapter_html:
                    chapter_html = replace_base64_images(chapter_html)
                    changed = True
                new_content.append(chapter_html)
            if changed:
                book.content = new_content
                # Rebuild preview_content with cleaned HTML
                book.preview_content = book.content[:2]

        if changed:
            db.session.add(book)

    db.session.commit()
    print("\n✓ Migration complete.")

if __name__ == '__main__':
    with app.app_context():
        ensure_column()
        migrate()
