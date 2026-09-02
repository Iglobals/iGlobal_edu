"""
Book chapter/page CONTENT storage in MongoDB.

Book metadata (title, author, price_naira, the chapter TITLES list, etc.)
stays in Postgres via models.Book - only the actual HTML content per page
lives here, in a `book_pages` collection, one document per page:

    {book_id, chapter_index, page_index, content_html, created_at, updated_at}

Why a page collection instead of embedding pages inside one Book document:
the whole point of this migration is to stop loading and slicing one giant
blob just to serve a single page - a page fetch is now a direct, indexed
query instead of "load the chapter, then slice it."

Phase 1 (this migration): every existing chapter becomes exactly ONE page
(page_index=0) holding its full existing HTML unchanged - no automatic
splitting, since "page" was deliberately defined as a manual, admin-authored
break, and the paginated editor that lets an admin actually create page 2+
hasn't been built yet. get_chapter_html() concatenates a chapter's pages
back into one HTML string so reading.html / the current (still-one-blob)
admin editor keep working unmodified until that rework lands.

admin_create_book/admin_edit_book still submit one whole HTML blob per
chapter (chapter_contents[]), and replace the ENTIRE chapters/content array
on every save (never an incremental diff) - see admin_routes.py. Mirroring
that exactly here avoids stale leftover pages when a book gets shorter.
"""
from datetime import datetime

from flask import current_app


def _pages_collection():
    return current_app.mongo['book_pages']


def get_chapter_pages(book_id: int, chapter_index: int):
    """Ordered list of page docs for one chapter."""
    col = _pages_collection()
    return list(col.find({'book_id': book_id, 'chapter_index': chapter_index}).sort('page_index', 1))


def get_chapter_html(book_id: int, chapter_index: int):
    """Concatenates a chapter's pages into one HTML string. Returns None if
    the chapter has no pages (not migrated yet, or doesn't exist)."""
    pages = get_chapter_pages(book_id, chapter_index)
    if not pages:
        return None
    return ''.join(p['content_html'] for p in pages)


def replace_all_chapters(book_id: int, chapter_htmls: list):
    """Wholesale replace of every chapter's content for a book - mirrors how
    admin_create_book/admin_edit_book already treat the chapters/content
    arrays as one whole thing to overwrite on every save."""
    col = _pages_collection()
    now = datetime.utcnow()

    for i, html in enumerate(chapter_htmls):
        col.update_one(
            {'book_id': book_id, 'chapter_index': i, 'page_index': 0},
            {'$set': {'content_html': html, 'updated_at': now},
             '$setOnInsert': {'created_at': now}},
            upsert=True,
        )

    # Drop chapters beyond the new count (book got shorter), and any
    # leftover multi-page chapters beyond page 0 (irrelevant until the
    # paginated editor exists, but harmless to guard against now).
    col.delete_many({'book_id': book_id, '$or': [
        {'chapter_index': {'$gte': len(chapter_htmls)}},
        {'chapter_index': {'$lt': len(chapter_htmls)}, 'page_index': {'$gt': 0}},
    ]})


def delete_book(book_id: int):
    """Called from admin_delete_book so Mongo doesn't accumulate orphaned
    pages for a book that no longer exists in Postgres."""
    _pages_collection().delete_many({'book_id': book_id})


def ensure_indexes(mongo_db):
    """Call once at startup (see app.py) - safe/idempotent to call repeatedly."""
    mongo_db['book_pages'].create_index([('book_id', 1), ('chapter_index', 1), ('page_index', 1)], unique=True)
