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

"Page" is a manual, admin-authored break (not automatic/size-based) - an
admin explicitly starts a new page while editing, or the docx importer
detects an explicit manual page break the source Word doc's author inserted
(see admin_routes.py's parse-docx route and docx_pages.py). Real page 2+
support now exists via replace_book_pages()/get_book_pages() -
replace_all_chapters() is kept only as a one-page-per-chapter compatibility
shim for older scripts.

admin_create_book/admin_edit_book replace the ENTIRE book's page structure
on every save (never an incremental diff), same as the old
chapters/content-array approach - avoids stale leftover pages when a
chapter or the book gets shorter.
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
    """Legacy single-page-per-chapter writer - kept only for scripts/back-
    compat (migrate_books_to_mongo.py). New code should use
    replace_book_pages() below, which accepts real per-chapter page lists."""
    replace_book_pages(book_id, [[html] for html in chapter_htmls])


def replace_book_pages(book_id: int, chapters_pages: list):
    """Wholesale replace of a book's entire page structure.

    `chapters_pages` is a list of chapters, each a list of page HTML strings
    in order, e.g. [["ch1 page1", "ch1 page2"], ["ch2 page1"]]. Mirrors how
    admin_create_book/admin_edit_book already treat the whole book's content
    as one thing to overwrite on every save, now just one level deeper.
    """
    col = _pages_collection()
    now = datetime.utcnow()

    for chapter_index, pages in enumerate(chapters_pages):
        for page_index, html in enumerate(pages):
            col.update_one(
                {'book_id': book_id, 'chapter_index': chapter_index, 'page_index': page_index},
                {'$set': {'content_html': html, 'updated_at': now},
                 '$setOnInsert': {'created_at': now}},
                upsert=True,
            )
        # Drop leftover pages beyond this chapter's new page count (chapter
        # got shorter - e.g. two pages merged back into one).
        col.delete_many({'book_id': book_id, 'chapter_index': chapter_index, 'page_index': {'$gte': len(pages)}})

    # Drop chapters beyond the new count entirely (book got shorter).
    col.delete_many({'book_id': book_id, 'chapter_index': {'$gte': len(chapters_pages)}})


def get_book_pages(book_id: int):
    """Every page for a book, in order - used by the admin editor to load a
    book for editing (needs all chapters x pages at once, not one at a time)."""
    col = _pages_collection()
    docs = list(col.find({'book_id': book_id}).sort([('chapter_index', 1), ('page_index', 1)]))
    chapters = {}
    for d in docs:
        chapters.setdefault(d['chapter_index'], []).append(d['content_html'])
    if not chapters:
        return []
    return [chapters.get(i, []) for i in range(max(chapters.keys()) + 1)]


def delete_book(book_id: int):
    """Called from admin_delete_book so Mongo doesn't accumulate orphaned
    pages for a book that no longer exists in Postgres."""
    _pages_collection().delete_many({'book_id': book_id})


def ensure_indexes(mongo_db):
    """Call once at startup (see app.py) - safe/idempotent to call repeatedly."""
    mongo_db['book_pages'].create_index([('book_id', 1), ('chapter_index', 1), ('page_index', 1)], unique=True)
