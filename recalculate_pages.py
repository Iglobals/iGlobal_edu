"""
Utility script to recalculate page counts for all books
This will be needed after Phase 2 is implemented with the improved pagination logic.

For now, this sets up the structure. The actual page calculation will happen
in the browser and be sent back to update these fields.

Usage:
    python recalculate_pages.py
    python recalculate_pages.py --book-id 5  # Recalculate specific book
"""

import argparse
from app import app, db
from models import Book


def initialize_page_counts(book_id=None):
    """
    Initialize page_counts to empty arrays for books that don't have it yet.
    After Phase 2, this will trigger actual page calculation.
    """
    with app.app_context():
        if book_id:
            books = Book.query.filter_by(id=book_id).all()
            if not books:
                print(f"✗ Book with ID {book_id} not found")
                return
        else:
            books = Book.query.all()
        
        updated_count = 0
        for book in books:
            # Initialize with empty structure if not set
            if book.page_counts is None:
                chapter_count = len(book.chapters) if book.chapters else 0
                # Initialize with zeros - will be calculated properly in Phase 2
                book.page_counts = [0] * chapter_count
                book.total_pages = 0
                updated_count += 1
        
        if updated_count > 0:
            db.session.commit()
            print(f"✓ Initialized page counts for {updated_count} book(s)")
        else:
            print("✓ All books already have page_counts initialized")
        
        # Show summary
        print("\nBook Summary:")
        for book in books:
            chapter_count = len(book.chapters) if book.chapters else 0
            print(f"  Book #{book.id}: {book.title}")
            print(f"    Chapters: {chapter_count}")
            print(f"    Page Counts: {book.page_counts}")
            print(f"    Total Pages: {book.total_pages}")
            print()


def update_book_pages(book_id, page_counts_array):
    """
    Update a specific book's page counts.
    Called from the admin interface after page calculation.
    
    Args:
        book_id: Book ID
        page_counts_array: List of integers [12, 15, 8, ...] representing pages per chapter
    """
    with app.app_context():
        book = Book.query.get(book_id)
        if not book:
            return False, "Book not found"
        
        if not isinstance(page_counts_array, list):
            return False, "page_counts must be an array"
        
        book.page_counts = page_counts_array
        book.total_pages = sum(page_counts_array)
        db.session.commit()
        
        return True, f"Updated book {book.title}: {book.total_pages} total pages across {len(page_counts_array)} chapters"


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Recalculate book page counts')
    parser.add_argument('--book-id', type=int, help='Specific book ID to recalculate')
    args = parser.parse_args()
    
    print("=" * 60)
    print("Book Page Count Initialization")
    print("=" * 60)
    print()
    
    initialize_page_counts(args.book_id)
    
    print("\nNote: Actual page calculation will be implemented in Phase 2.")
    print("For now, all page counts are set to 0.")
