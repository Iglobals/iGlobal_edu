from app import app
from extensions import db
from models import Book
from exam_packages import parse_title_exam_package

def get_preface_content():
    return '''<div class="preface">
<h1 class="text-3xl font-bold text-[#2F1341] mb-6">Preface</h1>
<p class="mb-4 text-lg leading-relaxed">Welcome to the JUPEB Keypoints series. This comprehensive guide has been meticulously crafted to help you excel in your Joint Universities Preliminary Examinations Board (JUPEB) examinations.</p>
<p class="mb-4 leading-relaxed">Our approach is built on three core principles:</p>
<ul class="list-disc ml-6 mb-4 space-y-2">
<li><strong>Exam-Focused Content:</strong> Every topic is aligned directly to the JUPEB syllabus</li>
<li><strong>Practical Application:</strong> Real exam questions and worked solutions</li>
<li><strong>Strategic Learning:</strong> Time-tested techniques from top scorers</li>
</ul>
<p class="mb-4 leading-relaxed">This book is designed to be your companion throughout your JUPEB journey. Use it alongside your regular textbooks, practice consistently, and success will follow.</p>
<p class="mb-4 leading-relaxed">We wish you the very best in your examinations.</p>
<p class="font-semibold">The iGlobals Editorial Team</p>
</div>'''

def get_toc_content(chapters):
    toc = '<div class="table-of-contents"><h1 class="text-3xl font-bold text-[#2F1341] mb-6">Table of Contents</h1><ol class="space-y-3">'
    for i, chapter in enumerate(chapters[2:], 1):  # Skip preface and TOC
        toc += f'<li class="flex justify-between border-b pb-2"><span class="font-semibold">{i}. {chapter}</span><span class="text-gray-500">Page {i}</span></li>'
    toc += '</ol></div>'
    return toc

def seed_books():
    """Seed the database with JUPEB Keypoints books"""
    
    books_data = []
    
    # SCIENCE BOOKS (₦1999 each)
    science_books = [
        {
            'title': 'JUPEB KEYPOINTS FOR MATHEMATICS',
            'author': 'Prof. Emeka Eze',
            'category': 'Science',
            'description': 'Comprehensive guide covering all JUPEB Mathematics topics with solved examples, practice questions, and exam strategies.',
            'image_url': 'https://i.ibb.co/RGWHftZk/IGLOBALS-MATHS-044519-jpg.jpg',
            'price_naira': 1999.0,
            'is_free': False,
        },
        {
            'title': 'JUPEB KEYPOINTS FOR PHYSICS',
            'author': 'Dr. Chidi Okonkwo',
            'category': 'Science',
            'description': 'Master Physics concepts with detailed explanations, diagrams, and past question analysis for JUPEB success.',
            'image_url': 'https://i.ibb.co/KcDk1GzP/iglobals-physics-044503-jpg.jpg',
            'price_naira': 1999.0,
            'is_free': False,
        },
        {
            'title': 'JUPEB KEYPOINTS FOR BIOLOGY',
            'author': 'Dr. Tunde Adeyemi',
            'category': 'Science',
            'description': 'Complete Biology coverage from cell structure to ecology with diagrams, definitions, and exam techniques.',
            'image_url': 'https://i.ibb.co/3yZnJYGm/iglobals-biology-044443-jpg.jpg',
            'price_naira': 1999.0,
            'is_free': False,
        },
        {
            'title': 'JUPEB KEYPOINTS FOR CHEMISTRY',
            'author': 'Prof. Ada Nwosu',
            'category': 'Science',
            'description': 'Detailed Chemistry guide covering organic, inorganic, and physical chemistry with practical examples.',
            'image_url': 'https://i.ibb.co/Jjvwg5V0/iglobals-chemistry-044512-jpg.jpg',
            'price_naira': 1999.0,
            'is_free': False,
        },
    ]
    
    # ARTS BOOKS (₦1999 each)
    arts_books = [
        {
            'title': 'JUPEB KEYPOINTS FOR GOVERNMENT',
            'author': 'Dr. Amaka Chukwu',
            'category': 'Arts & Humanities',
            'description': 'Comprehensive Government studies covering political systems, Nigerian politics, and international relations.',
            'image_url': 'https://i.ibb.co/YF7Z23vy/IGLOBALS-GOVERNMENT-120727-jpg.jpg',
            'price_naira': 1999.0,
            'is_free': False,
        },
        {
            'title': 'JUPEB KEYPOINTS FOR LITERATURE-IN-ENGLISH',
            'author': 'Prof. Chinwe Okoro',
            'category': 'Arts & Humanities',
            'description': 'Master literary analysis, prose, poetry, and drama with detailed text analysis and essay techniques.',
            'image_url': 'https://i.ibb.co/Q3cSHg1C/iglobals-lit-in-eng-120719-jpg.jpg',
            'price_naira': 1999.0,
            'is_free': False,
        },
        {
            'title': 'JUPEB KEYPOINTS FOR ECONOMICS',
            'author': 'Dr. Ngozi Okafor',
            'category': 'Arts & Humanities',
            'description': 'Complete Economics guide with demand-supply analysis, market structures, and macroeconomic principles.',
            'image_url': 'https://i.ibb.co/YFJzjp9N/IGLOBALS-ECONOMICS-120709-jpg.jpg',
            'price_naira': 1999.0,
            'is_free': False,
        },
        {
            'title': 'JUPEB KEYPOINTS FOR CHRISTIAN RELIGIOUS STUDIES',
            'author': 'Rev. Dr. Samuel Adebayo',
            'category': 'Arts & Humanities',
            'description': 'Detailed CRS coverage of Old and New Testament with theological concepts and moral teachings.',
            'image_url': 'https://i.ibb.co/N2DK8cZb/iglobals-crs-120738-jpg.jpg',
            'price_naira': 1999.0,
            'is_free': False,
        },
    ]
    
    # COMMERCIAL BOOKS (₦1999 each)
    commercial_books = [
        {
            'title': 'JUPEB KEYPOINTS FOR ACCOUNTING',
            'author': 'Dr. Oluwaseun Balogun',
            'category': 'Commercial',
            'description': 'Master double-entry bookkeeping, financial statements, and accounting principles for JUPEB.',
            'image_url': 'https://i.ibb.co/fdsX2sPH/iglobals-accounting-121210-jpg.jpg',
            'price_naira': 1999.0,
            'is_free': False,
        },
        {
            'title': 'JUPEB KEYPOINTS FOR BUSINESS STUDIES',
            'author': 'Prof. Funmi Adeleke',
            'category': 'Commercial',
            'description': 'Comprehensive Business Studies covering business organization, marketing, and management principles.',
            'image_url': 'https://i.ibb.co/fVNFxGM3/iglobals-business-121230-jpg.jpg',
            'price_naira': 1999.0,
            'is_free': False,
        },
    ]
    
    # COMBINATION BOOKS (₦4999 each)
    combination_books = [
        {
            'title': 'THREE-IN-ONE JUPEB MASTER KEYPOINT FOR SCIENCE (Maths, Physics, Chemistry)',
            'author': 'iGlobals Science Team',
            'category': 'Science',
            'description': 'Complete Science combination covering Mathematics, Physics, and Chemistry in one comprehensive package. Save ₦1,998!',
            'image_url': 'https://images.unsplash.com/photo-1532094349884-543bc11b234d?w=600&q=80',
            'price_naira': 4999.0,
            'is_free': False,
        },
        {
            'title': 'THREE-IN-ONE JUPEB MASTER KEYPOINT FOR SCIENCE (Physics, Chemistry, Biology)',
            'author': 'iGlobals Science Team',
            'category': 'Science',
            'description': 'Complete Science combination covering Physics, Chemistry, and Biology in one comprehensive package. Save ₦1,998!',
            'image_url': 'https://images.unsplash.com/photo-1532094349884-543bc11b234d?w=600&q=80',
            'price_naira': 4999.0,
            'is_free': False,
        },
        {
            'title': 'THREE-IN-ONE JUPEB MASTER KEYPOINT FOR ARTS (Government, CRS, Literature)',
            'author': 'iGlobals Arts Team',
            'category': 'Arts & Humanities',
            'description': 'Complete Arts combination covering Government, Christian Religious Studies, and Literature in one package. Save ₦1,998!',
            'image_url': 'https://images.unsplash.com/photo-1457369804613-52c61a468e7d?w=600&q=80',
            'price_naira': 4999.0,
            'is_free': False,
        },
        {
            'title': 'THREE-IN-ONE JUPEB MASTER KEYPOINT FOR ARTS (Literature, CRS, Economics)',
            'author': 'iGlobals Arts Team',
            'category': 'Arts & Humanities',
            'description': 'Complete Arts combination covering Literature, Christian Religious Studies, and Economics in one package. Save ₦1,998!',
            'image_url': 'https://images.unsplash.com/photo-1457369804613-52c61a468e7d?w=600&q=80',
            'price_naira': 4999.0,
            'is_free': False,
        },
        {
            'title': 'THREE-IN-ONE JUPEB MASTER KEYPOINT FOR COMMERCIAL (Government, Economics, Business)',
            'author': 'iGlobals Commercial Team',
            'category': 'Commercial',
            'description': 'Complete Commercial combination covering Government, Economics, and Business Studies in one package. Save ₦1,998!',
            'image_url': 'https://i.ibb.co/9H3g6RtK/iglobals-gov-coomercial-121237-jpg.jpg',
            'price_naira': 4999.0,
            'is_free': False,
        },
        {
            'title': 'THREE-IN-ONE JUPEB MASTER KEYPOINT FOR COMMERCIAL (Accounting, Economics, Business)',
            'author': 'iGlobals Commercial Team',
            'category': 'Commercial',
            'description': 'Complete Commercial combination covering Accounting, Economics, and Business Studies in one package. Save ₦1,998!',
            'image_url': 'https://i.ibb.co/4nZPp9gg/iglobals-econs-commercial-121219-jpg.jpg',
            'price_naira': 4999.0,
            'is_free': False,
        },
    ]
    
    # FREE BOOK
    free_book = {
        'title': 'JUPEB MASTERY GUIDE - FREE EDITION',
        'author': 'iGlobals Editorial Team',
        'category': 'JUPEB Mastery',
        'description': 'Free comprehensive guide to understanding JUPEB, exam strategies, and study techniques for all faculties.',
        'image_url': 'https://images.unsplash.com/photo-1427504494785-3a9ca7044f45?w=600&q=80',
        'price_naira': 0.0,
        'is_free': True,
    }
    
    # Combine all books
    all_books = science_books + commercial_books + arts_books + combination_books + [free_book]
    
    # Add chapters and content to each book
    for book in all_books:
        # JUPEB exam-access package inferred from the title (see exam_packages.py) -
        # single subject: 1 exam key + N1,000 add-on; THREE-IN-ONE: 3 keys + N2,000.
        book['exam_keys'], book['exam_addon_price_naira'] = parse_title_exam_package(book['title'])

        if 'THREE-IN-ONE' in book['title']:
            # Combination books have more chapters
            book['chapters'] = [
                'Preface',
                'Table of Contents',
                'Part 1: Subject Overview',
                'Part 2: Key Concepts',
                'Part 3: Worked Examples',
                'Part 4: Practice Questions',
                'Part 5: Past Questions Analysis',
                'Part 6: Exam Strategies',
                'Part 7: Quick Reference Guide',
                'Part 8: Final Tips'
            ]
        else:
            book['chapters'] = [
                'Preface',
                'Table of Contents',
                'Chapter 1: Introduction',
                'Chapter 2: Core Concepts',
                'Chapter 3: Advanced Topics',
                'Chapter 4: Practice Questions',
                'Chapter 5: Past Questions',
                'Chapter 6: Exam Strategies'
            ]
        
        # Generate content
        book['content'] = [
            get_preface_content(),
            get_toc_content(book['chapters']),
        ]
        
        # Add detailed chapter content
        for i, chapter in enumerate(book['chapters'][2:], 1):  # Skip preface and TOC
            content = f'''<div class="chapter">
<h1 class="text-3xl font-bold text-[#2F1341] mb-6 font-condensed">{chapter}</h1>

<div class="chapter-intro mb-8">
<p class="text-lg leading-relaxed mb-4">This chapter provides comprehensive coverage of essential topics that frequently appear in JUPEB examinations. Each section has been carefully structured to build your understanding progressively.</p>
</div>

<div class="section mb-8">
<h2 class="text-2xl font-bold text-[#2F1341] mb-4">Section {i}.1: Key Concepts</h2>
<p class="mb-4 leading-relaxed">Understanding the fundamental concepts is crucial for success. The JUPEB examiners consistently test your ability to apply these principles in various contexts.</p>
<p class="mb-4 leading-relaxed">Let's break down the core ideas step by step. First, ensure you can define each term precisely. The examiner awards marks for accuracy and clarity in definitions.</p>
<ul class="list-disc ml-6 mb-4 space-y-2">
<li>Master the basic terminology and definitions</li>
<li>Understand the relationships between different concepts</li>
<li>Practice applying concepts to real-world scenarios</li>
<li>Review past questions to identify common patterns</li>
</ul>
</div>

<div class="section mb-8">
<h2 class="text-2xl font-bold text-[#2F1341] mb-4">Section {i}.2: Worked Examples</h2>
<p class="mb-4 leading-relaxed">The best way to master any topic is through practice. Here are carefully selected examples that mirror actual JUPEB questions.</p>

<div class="example bg-gray-50 p-6 rounded-lg mb-4">
<h3 class="font-bold text-lg mb-3">Example {i}.1</h3>
<p class="mb-3"><strong>Question:</strong> This is a sample question that demonstrates the type of problems you'll encounter in the examination.</p>
<p class="mb-3"><strong>Solution:</strong> Step-by-step solution showing the proper method and presentation expected by examiners.</p>
<p class="text-sm text-gray-600"><strong>Examiner's Tip:</strong> Always show your working clearly. Marks are awarded for method even if the final answer is incorrect.</p>
</div>

<div class="example bg-gray-50 p-6 rounded-lg mb-4">
<h3 class="font-bold text-lg mb-3">Example {i}.2</h3>
<p class="mb-3"><strong>Question:</strong> Another typical examination question with increasing complexity.</p>
<p class="mb-3"><strong>Solution:</strong> Detailed solution with annotations explaining each step.</p>
<p class="text-sm text-gray-600"><strong>Common Mistake:</strong> Many students make errors at this stage. Pay attention to the details.</p>
</div>
</div>

<div class="section mb-8">
<h2 class="text-2xl font-bold text-[#2F1341] mb-4">Section {i}.3: Practice Questions</h2>
<p class="mb-4 leading-relaxed">Now it's your turn to practice. Attempt these questions under timed conditions to simulate exam pressure.</p>

<div class="practice-questions space-y-4">
<div class="question p-4 border-l-4 border-[#B0522E]">
<p class="font-semibold mb-2">Question 1:</p>
<p>Practice question designed to test your understanding of the concepts covered.</p>
</div>
<div class="question p-4 border-l-4 border-[#B0522E]">
<p class="font-semibold mb-2">Question 2:</p>
<p>Another practice question with slightly different approach to test flexibility.</p>
</div>
<div class="question p-4 border-l-4 border-[#B0522E]">
<p class="font-semibold mb-2">Question 3:</p>
<p>Challenge question combining multiple concepts from this chapter.</p>
</div>
</div>
</div>

<div class="section mb-8">
<h2 class="text-2xl font-bold text-[#2F1341] mb-4">Section {i}.4: Exam Strategy</h2>
<p class="mb-4 leading-relaxed">Knowing the content is only half the battle. You must also know how to present your answers effectively.</p>

<div class="strategy-tips bg-[#2F1341] text-white p-6 rounded-lg">
<h3 class="font-bold text-xl mb-4">Top Tips for This Topic:</h3>
<ol class="space-y-3">
<li><strong>1. Time Management:</strong> Allocate your time wisely. Don't spend too long on any single question.</li>
<li><strong>2. Read Carefully:</strong> Understand what the question is asking before you start writing.</li>
<li><strong>3. Show Your Work:</strong> Even if you're unsure, write down your thought process.</li>
<li><strong>4. Check Your Answers:</strong> Always leave time to review your work.</li>
<li><strong>5. Practice Regularly:</strong> Consistent practice is the key to success.</li>
</ol>
</div>
</div>

<div class="chapter-summary mt-8 p-6 bg-gray-50 rounded-lg">
<h2 class="text-2xl font-bold text-[#2F1341] mb-4">Chapter Summary</h2>
<p class="mb-4">In this chapter, we covered the essential concepts, worked through examples, and provided practice questions. Make sure you:</p>
<ul class="list-disc ml-6 space-y-2">
<li>Understand all key definitions and concepts</li>
<li>Can solve problems independently</li>
<li>Know the common pitfalls to avoid</li>
<li>Have practiced under timed conditions</li>
</ul>
<p class="mt-4 font-semibold text-[#B0522E]">Next Chapter: Continue building on these foundations with more advanced topics.</p>
</div>
</div>'''
            book['content'].append(content)
    
    books_data = all_books
    
    with app.app_context():
        print("=" * 60)
        print("Seeding JUPEB Keypoints Books")
        print("=" * 60)
        
        # Check for existing books
        existing_count = Book.query.count()
        if existing_count > 0:
            print(f"\nFound {existing_count} existing books.")
            print("\n⚠️  WARNING: Cannot delete books due to foreign key constraints.")
            print("Books are referenced by other tables (library_items, purchases, etc.)")
            print("\nOptions:")
            print("  1. Keep existing books (recommended)")
            print("  2. Manually clear database: DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
            print("\nSkipping book deletion...")
            return
        
        # Add new books
        print(f"\n📚 Adding {len(books_data)} books...")
        for book_data in books_data:
            # preview_content = first 2 chapters only
            book_data['preview_content'] = book_data.get('content', [])[:2]
            book = Book(**book_data)
            db.session.add(book)
        
        db.session.commit()
        
        print("\n✅ Successfully seeded books!")
        print("\nBook Categories:")
        print(f"  - Science (Individual): 4 books @ ₦1,999 each")
        print(f"  - Commercial (Individual): 2 books @ ₦1,999 each")
        print(f"  - Arts (Individual): 4 books @ ₦1,999 each")
        print(f"  - Combinations: 6 books @ ₦4,999 each (Save ₦1,998!)")
        print(f"  - Free: 1 book")
        print(f"\nTotal: {len(books_data)} books")
        print("=" * 60)

if __name__ == '__main__':
    seed_books()