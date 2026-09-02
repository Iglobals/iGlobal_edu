"""
One-time backfill: copies every existing book's chapter HTML out of
Postgres's Book.content JSON column into MongoDB's book_pages collection
(one page per chapter, page_index=0 - see mongo_books.py for why).

After this runs and is verified, Book.content / Book.preview_content in
Postgres are dead columns (no code reads them anymore - routes.py/
admin_routes.py were switched to read from Mongo instead). They're left in
place rather than dropped, in case this needs to be rolled back.

Dry run by default - prints what it would do. Pass --yes to actually write.

Usage:
    python migrate_books_to_mongo.py            # dry run
    python migrate_books_to_mongo.py --yes       # actually migrate
"""
import sys

from app import app
from models import Book
import mongo_books


def main():
    do_write = '--yes' in sys.argv

    with app.app_context():
        books = Book.query.all()
        print(f"Found {len(books)} book(s) in Postgres.\n")

        for book in books:
            content = book.content or []
            existing_pages = sum(1 for i in range(len(content)) if mongo_books.get_chapter_html(book.id, i) is not None)

            print(f"Book {book.id} ({book.title!r}): {len(content)} chapter(s), "
                  f"{existing_pages} already in Mongo" + (" - skipping" if existing_pages == len(content) and content else ""))

            if not content:
                continue
            if existing_pages == len(content):
                continue  # already fully migrated - safe to re-run this script

            if do_write:
                mongo_books.replace_all_chapters(book.id, content)
                print(f"  -> migrated {len(content)} chapter(s) to Mongo")

        print()
        if do_write:
            print("Migration complete.")
        else:
            print("Dry run only - nothing was written. Re-run with --yes to actually migrate.")


if __name__ == '__main__':
    main()
