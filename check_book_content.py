#!/usr/bin/env python3
"""
Quick script to check if books have content in the database
"""

from app import app
from extensions import db
from models import Book

def check_books():
    with app.app_context():
        books = Book.query.all()
        
        print("=" * 80)
        print("BOOK CONTENT CHECK")
        print("=" * 80)
        
        if not books:
            print("\n❌ No books found in database!")
            print("\nRun: python seed_data.py")
            return
        
        print(f"\nFound {len(books)} books\n")
        
        for book in books:
            print(f"\n📚 {book.title}")
            print(f"   ID: {book.id}")
            print(f"   Chapters: {len(book.chapters) if book.chapters else 0}")
            print(f"   Content: {len(book.content) if book.content else 0}")
            
            if not book.content or len(book.content) == 0:
                print(f"   ❌ NO CONTENT!")
            elif len(book.chapters) != len(book.content):
                print(f"   ⚠️  MISMATCH: {len(book.chapters)} chapters but {len(book.content)} content items")
            else:
                print(f"   ✅ Content OK")
                # Show first chapter preview
                if book.content[0]:
                    preview = book.content[0][:100].replace('\n', ' ')
                    print(f"   Preview: {preview}...")
        
        print("\n" + "=" * 80)
        
        # Summary
        books_with_content = sum(1 for b in books if b.content and len(b.content) > 0)
        books_without_content = len(books) - books_with_content
        
        print(f"\nSummary:")
        print(f"  ✅ Books with content: {books_with_content}")
        print(f"  ❌ Books without content: {books_without_content}")
        
        if books_without_content > 0:
            print(f"\n⚠️  {books_without_content} books need content!")
            print(f"\nTo fix: python seed_data.py")
        
        print("=" * 80)

if __name__ == '__main__':
    check_books()
