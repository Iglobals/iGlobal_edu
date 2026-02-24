# Admin Editor Pre-population Debugging Guide

## How It Works

The admin edit book page uses Quill.js rich text editors. Here's the flow:

### 1. Template Rendering (Server-side)
```html
<!-- Hidden textarea with existing content -->
<textarea name="chapter_contents[]" class="hidden chapter-content">
    {{ book.content[i]|safe if i < book.content|length else '' }}
</textarea>

<!-- Quill editor container (empty initially) -->
<div class="chapter-editor"></div>
```

### 2. JavaScript Initialization (Client-side)
```javascript
// 1. Find all editor containers and textareas
const editorElements = document.querySelectorAll('.chapter-editor');
const contentTextareas = document.querySelectorAll('.chapter-content');

// 2. For each editor
editorElements.forEach((editorEl, index) => {
    // Initialize Quill
    const editor = new Quill(editorEl, {...});
    
    // Get content from hidden textarea
    const textarea = contentTextareas[index];
    const content = textarea.value;
    
    // Load content into editor
    if (content) {
        editor.root.innerHTML = content;
    }
});
```

## Debugging Steps

### Step 1: Check Browser Console
1. Open the edit book page
2. Press F12 to open Developer Tools
3. Go to Console tab
4. Look for these messages:

```
=== Quill Editor Initialization ===
Found editors: X
Found textareas: X
Chapter 1:
  - Content length: XXXX
  - First 100 chars: <div class="preface">...
  ✓ Loaded content for chapter 1
...
=== Initialization Complete ===
```

### Step 2: Check What You See

**If you see:**
- ✅ `Content length: 0` → The database has no content
- ✅ `Content length: XXXX` but editor is empty → Content loading issue
- ✅ `No textarea found` → Template rendering issue

### Step 3: Verify Database Content

Check if the book actually has content in the database:

```python
# In Python shell or script
from app import app
from extensions import db
from models import Book

with app.app_context():
    book = Book.query.get(BOOK_ID)  # Replace with your book ID
    print(f"Chapters: {len(book.chapters)}")
    print(f"Content: {len(book.content)}")
    
    for i, content in enumerate(book.content):
        print(f"\nChapter {i+1}:")
        print(f"  Length: {len(content)}")
        print(f"  Preview: {content[:100]}")
```

### Step 4: Check HTML Source

1. Right-click on the page → View Page Source
2. Search for `chapter-content`
3. Check if the textarea has content:

```html
<!-- Should look like this: -->
<textarea name="chapter_contents[]" class="hidden chapter-content">
    <div class="preface">
    <h1 class="text-3xl font-bold text-[#2F1341] mb-6">Preface</h1>
    ...
    </div>
</textarea>

<!-- NOT like this: -->
<textarea name="chapter_contents[]" class="hidden chapter-content"></textarea>
```

## Common Issues & Solutions

### Issue 1: Database Has No Content
**Symptom:** Console shows `Content length: 0`

**Solution:** Run the seed script to populate books with content:
```bash
python seed_data.py
```

### Issue 2: Content Not Escaped Properly
**Symptom:** HTML shows escaped characters like `&lt;` instead of `<`

**Solution:** The template uses `|safe` filter, which should work. Check if it's present:
```html
{{ book.content[i]|safe if i < book.content|length else '' }}
```

### Issue 3: Quill Not Loading
**Symptom:** Console shows errors about Quill

**Solution:** Check if Quill CDN is loaded:
```html
<link href="https://cdn.quilljs.com/1.3.6/quill.snow.css" rel="stylesheet">
<script src="https://cdn.quilljs.com/1.3.6/quill.js"></script>
```

### Issue 4: Timing Issue
**Symptom:** Editors initialize before content is ready

**Solution:** Already handled with `DOMContentLoaded` event. If still issues, add delay:
```javascript
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(function() {
        // Initialize editors
    }, 100);
});
```

### Issue 5: Content Array Shorter Than Chapters Array
**Symptom:** Some chapters load, others don't

**Solution:** Template already handles this:
```html
{{ book.content[i]|safe if i < book.content|length else '' }}
```

But verify in database:
```python
book = Book.query.get(BOOK_ID)
print(f"Chapters: {len(book.chapters)}")
print(f"Content: {len(book.content)}")
# These should match!
```

## Manual Testing

### Test 1: Create New Book
1. Go to Admin → Books → Create New Book
2. Add title, author, etc.
3. Add 2-3 chapters with content
4. Save
5. Go back and edit the book
6. Check if content appears in editors

### Test 2: Check Existing Book
1. Find a book that should have content
2. Click Edit
3. Open browser console (F12)
4. Check the debug messages
5. Verify content appears

### Test 3: Verify Save Works
1. Edit a book
2. Make a small change in an editor
3. Save
4. Edit again
5. Verify the change persisted

## Quick Fix Script

If books have no content, run this to add sample content:

```python
from app import app
from extensions import db
from models import Book

with app.app_context():
    books = Book.query.all()
    
    for book in books:
        if not book.content or len(book.content) == 0:
            # Add sample content for each chapter
            book.content = []
            for i, chapter in enumerate(book.chapters):
                content = f'''<div class="chapter">
<h1 class="text-3xl font-bold text-[#2F1341] mb-6">{chapter}</h1>
<p class="mb-4">This is sample content for {chapter}. Edit this to add your actual content.</p>
<p class="mb-4">You can use the rich text editor to format your content with:</p>
<ul class="list-disc ml-6 mb-4">
<li>Bold, italic, and underline text</li>
<li>Headers and subheaders</li>
<li>Ordered and unordered lists</li>
<li>Links</li>
</ul>
</div>'''
                book.content.append(content)
            
            db.session.commit()
            print(f"Added content to: {book.title}")
    
    print("Done!")
```

## Expected Behavior

When everything works correctly:

1. **Page Load:**
   - Console shows initialization messages
   - Each chapter shows content length
   - Editors display formatted content

2. **Editing:**
   - You can type and format text
   - Toolbar buttons work
   - Content updates in real-time

3. **Saving:**
   - Console shows "Saving editor content..."
   - Each chapter's content length is logged
   - Form submits successfully

4. **After Save:**
   - Redirect to books list
   - Success message appears
   - Editing again shows updated content

## Still Not Working?

If you've tried everything above and it still doesn't work:

1. **Check the actual error:**
   - Open browser console
   - Look for red error messages
   - Share the exact error message

2. **Verify the book ID:**
   - Make sure you're editing a book that exists
   - Check the URL: `/admin/books/edit/<book_id>`

3. **Check database connection:**
   - Verify PostgreSQL is running
   - Check .env file has correct credentials

4. **Try a different browser:**
   - Sometimes browser extensions interfere
   - Try Chrome/Firefox in incognito mode

5. **Check server logs:**
   - Look for Python errors in the terminal
   - Check if the route is being called

## Contact Information

If you need help:
1. Share the browser console output
2. Share any Python errors from terminal
3. Confirm which book ID you're trying to edit
4. Confirm if the book has content in database
