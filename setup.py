#!/usr/bin/env python3
"""
iGlobals Educational Services - Complete Setup Script
Run this after installing PostgreSQL and creating the database
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Check DATABASE_URL before importing app
database_url = os.getenv('DATABASE_URL')
if not database_url:
    print("\n✗ DATABASE_URL not found in .env file")
    print("\nPlease ensure your .env file contains:")
    print("DATABASE_URL=postgresql://profeso1012:secured123@localhost:5432/iglobals_db")
    sys.exit(1)

try:
    from app import app
    from extensions import db
    from models import User, Book, Purchase
    from werkzeug.security import generate_password_hash
except ImportError as e:
    print(f"\n✗ Import error: {e}")
    print("\nPlease ensure all dependencies are installed:")
    print("pip install -r requirements.txt")
    sys.exit(1)

def setup_database():
    """Create all database tables"""
    print("\n📦 Creating database tables...")
    try:
        with app.app_context():
            db.create_all()
        print("   ✓ Database tables created successfully!")
        return True
    except Exception as e:
        print(f"   ✗ Failed to create tables: {e}")
        return False

def create_admin():
    """Create default admin user"""
    print("\n👤 Creating admin user...")
    try:
        with app.app_context():
            # Check if admin already exists
            existing_admin = User.query.filter_by(email='admin@iglobals.com').first()
            if existing_admin:
                print("   ⚠  Admin user already exists!")
                print(f"   Email: admin@iglobals.com")
                return True
            
            admin = User(
                full_name='Admin User',
                email='admin@iglobals.com',
                password_hash=generate_password_hash('admin123'),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
        
        print("   ✓ Admin user created successfully!")
        print("\n   " + "="*50)
        print("   ADMIN CREDENTIALS")
        print("   " + "="*50)
        print("   Email:    admin@iglobals.com")
        print("   Password: admin123")
        print("   " + "="*50)
        print("\n   ⚠  IMPORTANT: Change this password after first login!")
        return True
        
    except Exception as e:
        print(f"   ✗ Failed to create admin: {e}")
        return False

def seed_books():
    """Seed database with sample books"""
    print("\n📚 Seeding sample books...")
    
    books_data = [
        {
            'title': 'Scientific Inquiries Vol. I',
            'author': 'Prof. Emeka Eze',
            'category': 'Science',
            'description': 'Targeted formulas and techniques for rigorous scientific examinations.',
            'image_url': 'https://images.unsplash.com/photo-1532094349884-543bc11b234d?w=600&q=80',
            'price_naira': 5000.0,
            'is_free': False,
            'chapters': [
                'Chapter 1: Forces & Motion',
                'Chapter 2: Chemical Reactions',
                'Chapter 3: Cell Biology',
                'Chapter 4: Waves & Optics',
                'Chapter 5: Organic Chemistry',
                'Chapter 6: Genetics & Heredity',
                'Chapter 7: Exam Strategy & Past Q'
            ],
            'content': [
                '<h2 class="text-2xl font-bold text-[#6B2D5C] mb-6 font-condensed">Chapter 1: Forces & Motion</h2><p class="mb-4">Understanding Newton\'s laws is the backbone of JUPEB Physics. The examiner consistently sets questions around the three laws of motion — and the trick is not just to state them, but to apply them to real scenarios within a strict time limit.</p><p class="mb-4">Start with free-body diagrams. Before writing a single equation, draw out all forces acting on the object. Label each force clearly: weight (W = mg), normal reaction (N), tension (T), and friction (f = μN).</p><p class="mb-4">Newton\'s second law (F = ma) is the workhorse of mechanics questions. Watch for questions where multiple forces act in different directions — resolve them into components first.</p>',
                '<h2 class="text-2xl font-bold text-[#6B2D5C] mb-6 font-condensed">Chapter 2: Chemical Reactions</h2><p class="mb-4">JUPEB Chemistry rewards students who can move quickly between symbolic, particulate, and macroscopic representations of reactions. Practice writing balanced equations daily.</p><p class="mb-4">Redox chemistry is heavily tested. Learn to assign oxidation numbers confidently and identify oxidation/reduction in half-equations.</p>',
                '<h2 class="text-2xl font-bold text-[#6B2D5C] mb-6 font-condensed">Chapter 3: Cell Biology</h2><p class="mb-4">Biology at JUPEB level rewards precision in definitions and accuracy in diagrams. Know the differences between prokaryotic and eukaryotic cells in detail.</p>',
                '<h2 class="text-2xl font-bold text-[#6B2D5C] mb-6 font-condensed">Chapter 4: Waves & Optics</h2><p class="mb-4">Waves questions test your ability to read and interpret wave diagrams. Practice with at least 20 different waveforms before the exam.</p>',
                '<h2 class="text-2xl font-bold text-[#6B2D5C] mb-6 font-condensed">Chapter 5: Organic Chemistry</h2><p class="mb-4">Homologous series form the foundation of organic chemistry. Know the general formula, functional group, and key reactions.</p>',
                '<h2 class="text-2xl font-bold text-[#6B2D5C] mb-6 font-condensed">Chapter 6: Genetics & Heredity</h2><p class="mb-4">Genetics questions range from simple Mendelian inheritance to dihybrid crosses. Master Punnett squares.</p>',
                '<h2 class="text-2xl font-bold text-[#6B2D5C] mb-6 font-condensed">Chapter 7: Exam Strategy</h2><p class="mb-4">The JUPEB Science paper is three hours long. Time management is crucial. Always plan before you write.</p>'
            ]
        },
        {
            'title': 'Business Analytics Mastery',
            'author': 'Dr. Ngozi Okafor',
            'category': 'Commercial',
            'description': 'Precise techniques for analytical and business-related examinations.',
            'image_url': 'https://images.unsplash.com/photo-1512820790803-83ca734da794?w=600&q=80',
            'price_naira': 4500.0,
            'is_free': False,
            'chapters': [
                'Chapter 1: Demand & Supply',
                'Chapter 2: Accounting Basics',
                'Chapter 3: Business Finance',
                'Chapter 4: Market Structures',
                'Chapter 5: Exam Strategy'
            ],
            'content': [
                '<h2 class="text-2xl font-bold text-[#6B2D5C] mb-6 font-condensed">Chapter 1: Demand & Supply</h2><p class="mb-4">The law of demand and supply underpins every Economics question. Draw demand and supply curves confidently.</p>',
                '<h2 class="text-2xl font-bold text-[#6B2D5C] mb-6 font-condensed">Chapter 2: Accounting Basics</h2><p class="mb-4">Double-entry bookkeeping: every debit has an equal and opposite credit. Master the DEAD CLIC mnemonic.</p>',
                '<h2 class="text-2xl font-bold text-[#6B2D5C] mb-6 font-condensed">Chapter 3: Business Finance</h2><p class="mb-4">Sources of finance — internal vs. external, short-term vs. long-term. Know advantages and disadvantages.</p>',
                '<h2 class="text-2xl font-bold text-[#6B2D5C] mb-6 font-condensed">Chapter 4: Market Structures</h2><p class="mb-4">Four market structures: perfect competition, monopolistic competition, oligopoly, and monopoly.</p>',
                '<h2 class="text-2xl font-bold text-[#6B2D5C] mb-6 font-condensed">Chapter 5: Exam Strategy</h2><p class="mb-4">The Commercial paper rewards speed and precision. Always include labelled diagrams in Economics essays.</p>'
            ]
        },
        {
            'title': 'Creative Strategies in Literature',
            'author': 'Dr. Amaka Chukwu',
            'category': 'Arts & Humanities',
            'description': 'Comprehensive strategies to master creative and theoretical subjects.',
            'image_url': 'https://images.unsplash.com/photo-1589998059171-988d887df646?w=600&q=80',
            'price_naira': 4000.0,
            'is_free': False,
            'chapters': [
                'Chapter 1: Literature in English',
                'Chapter 2: Government & Politics',
                'Chapter 3: CRS / IRS',
                'Chapter 4: Essay Technique',
                'Chapter 5: Exam Strategy'
            ],
            'content': [
                '<h2 class="text-2xl font-bold text-[#6B2D5C] mb-6 font-condensed">Chapter 1: Literature in English</h2><p class="mb-4">Literature tests knowledge of set texts, literary devices, and essay construction skills.</p>',
                '<h2 class="text-2xl font-bold text-[#6B2D5C] mb-6 font-condensed">Chapter 2: Government & Politics</h2><p class="mb-4">Government questions split between conceptual definitions and Nigerian political analysis.</p>',
                '<h2 class="text-2xl font-bold text-[#6B2D5C] mb-6 font-condensed">Chapter 3: CRS / IRS</h2><p class="mb-4">For CRS, focus on Old and New Testament narratives. For IRS, master the five pillars of Islam.</p>',
                '<h2 class="text-2xl font-bold text-[#6B2D5C] mb-6 font-condensed">Chapter 4: Essay Technique</h2><p class="mb-4">A strong Arts essay has four components: introduction, body paragraphs, evidence, and conclusion.</p>',
                '<h2 class="text-2xl font-bold text-[#6B2D5C] mb-6 font-condensed">Chapter 5: Exam Strategy</h2><p class="mb-4">The Arts paper is essay-heavy. Spend no more than 35 minutes per essay.</p>'
            ]
        },
        {
            'title': 'JUPEB Mastery Complete Guide',
            'author': 'iGlobals Editorial Team',
            'category': 'JUPEB Mastery',
            'description': 'Complete guide to understanding and conquering JUPEB examinations.',
            'image_url': 'https://images.unsplash.com/photo-1427504494785-3a9ca7044f45?w=600&q=80',
            'price_naira': 0.0,
            'is_free': True,
            'chapters': [
                'Chapter 1: Understanding JUPEB',
                'Chapter 2: Revision Planning',
                'Chapter 3: Exam Day Strategy',
                'Chapter 4: Mental Preparation'
            ],
            'content': [
                '<h2 class="text-2xl font-bold text-[#6B2D5C] mb-6 font-condensed">Chapter 1: Understanding JUPEB</h2><p class="mb-4">The Joint Universities Preliminary Examinations Board (JUPEB) is a rigorous pre-degree programme.</p>',
                '<h2 class="text-2xl font-bold text-[#6B2D5C] mb-6 font-condensed">Chapter 2: Revision Planning</h2><p class="mb-4">Consistency is the greatest predictor of JUPEB success. Build a 12-week revision plan.</p>',
                '<h2 class="text-2xl font-bold text-[#6B2D5C] mb-6 font-condensed">Chapter 3: Exam Day Strategy</h2><p class="mb-4">Sleep is not optional. Arrive early. Read through the question paper calmly before you begin.</p>',
                '<h2 class="text-2xl font-bold text-[#6B2D5C] mb-6 font-condensed">Chapter 4: Mental Preparation</h2><p class="mb-4">Exam anxiety is manageable. Practice controlled breathing: inhale for 4, hold for 4, exhale for 4.</p>'
            ]
        },
        {
            'title': 'JUPEB Past Questions & Answers',
            'author': 'iGlobals Research Unit',
            'category': 'Past Questions',
            'description': 'Comprehensive collection of past JUPEB questions with detailed solutions.',
            'image_url': 'https://images.unsplash.com/photo-1434030216411-0b793f4b6f62?w=600&q=80',
            'price_naira': 3500.0,
            'is_free': False,
            'chapters': [
                '2024 Science Paper',
                '2023 Commercial Paper',
                '2022 Arts Paper',
                '2021 High Frequency Topics',
                'Answer Techniques'
            ],
            'content': [
                '<h2 class="text-2xl font-bold text-[#6B2D5C] mb-6 font-condensed">2024 JUPEB Science</h2><p class="mb-4">Selected questions from the 2024 Science paper with detailed solutions.</p>',
                '<h2 class="text-2xl font-bold text-[#6B2D5C] mb-6 font-condensed">2023 Commercial Paper</h2><p class="mb-4">Key questions from Economics and Accounting papers with marking schemes.</p>',
                '<h2 class="text-2xl font-bold text-[#6B2D5C] mb-6 font-condensed">2022 Arts Paper</h2><p class="mb-4">Literature, Government, and CRS questions with model answers.</p>',
                '<h2 class="text-2xl font-bold text-[#6B2D5C] mb-6 font-condensed">2021 High Frequency Topics</h2><p class="mb-4">Analysis of topics that appear most frequently across all faculties.</p>',
                '<h2 class="text-2xl font-bold text-[#6B2D5C] mb-6 font-condensed">Answer Techniques</h2><p class="mb-4">How to structure answers for maximum marks. Show all working for calculations.</p>'
            ]
        },
        {
            'title': 'Chemistry & Biology Breakdown',
            'author': 'Dr. Tunde Adeyemi',
            'category': 'Science',
            'description': 'Detailed breakdown of Chemistry and Biology topics for JUPEB.',
            'image_url': 'https://images.unsplash.com/photo-1581093458791-9d42cc7bc59b?w=600&q=80',
            'price_naira': 0.0,
            'is_free': True,
            'chapters': [
                'Atomic Structure',
                'Chemical Bonding',
                'Cell Structure',
                'Photosynthesis & Respiration',
                'Ecology'
            ],
            'content': [
                '<h2 class="text-2xl font-bold text-[#6B2D5C] mb-6 font-condensed">Atomic Structure</h2><p class="mb-4">Know electronic configurations for elements Z = 1 to Z = 36 using the Aufbau principle.</p>',
                '<h2 class="text-2xl font-bold text-[#6B2D5C] mb-6 font-condensed">Chemical Bonding</h2><p class="mb-4">Three primary bond types: ionic, covalent, and metallic. Master Lewis diagrams.</p>',
                '<h2 class="text-2xl font-bold text-[#6B2D5C] mb-6 font-condensed">Cell Structure</h2><p class="mb-4">Plant vs. animal cell differences. Build a comparison table.</p>',
                '<h2 class="text-2xl font-bold text-[#6B2D5C] mb-6 font-condensed">Photosynthesis & Respiration</h2><p class="mb-4">Light-dependent and light-independent reactions. Aerobic respiration stages.</p>',
                '<h2 class="text-2xl font-bold text-[#6B2D5C] mb-6 font-condensed">Ecology</h2><p class="mb-4">Food chains, energy flow, nutrient cycling. Know nitrogen, carbon, and water cycles.</p>'
            ]
        }
    ]
    
    try:
        with app.app_context():
            # Check if books already exist
            existing_books = Book.query.count()
            if existing_books > 0:
                print(f"   ⚠  Database already has {existing_books} books!")
                response = input("   Do you want to clear and re-seed? (y/n): ")
                if response.lower() != 'y':
                    print("   Skipping book seeding...")
                    return True
                
                # Clear existing books
                Book.query.delete()
                db.session.commit()
                print("   Cleared existing books")
            
            # Add new books
            for book_data in books_data:
                book = Book(**book_data)
                db.session.add(book)
            
            db.session.commit()
            print(f"   ✓ Successfully seeded {len(books_data)} books!")
            return True
            
    except Exception as e:
        print(f"   ✗ Error seeding books: {e}")
        return False

def main():
    print("=" * 60)
    print("iGlobals Educational Services - Complete Setup")
    print("=" * 60)
    print(f"\nDatabase: {database_url.split('@')[1] if '@' in database_url else 'unknown'}")
    
    success = True
    
    # Step 1: Create tables
    if not setup_database():
        success = False
    
    # Step 2: Create admin (only if tables created successfully)
    if success and not create_admin():
        success = False
    
    # Step 3: Seed books (ask user)
    if success:
        print("\n" + "=" * 60)
        response = input("📚 Do you want to seed sample books? (y/n): ")
        if response.lower() == 'y':
            if not seed_books():
                success = False
    
    # Final status
    print("\n" + "=" * 60)
    if success:
        print("✅ SETUP COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print("\n📋 Next steps:")
        print("   1. Run the application:  python app.py")
        print("   2. Visit:                http://localhost:5000")
        print("   3. Admin panel:          http://localhost:5000/admin")
        print("\n🔐 Admin Login:")
        print("   Email:    admin@iglobals.com")
        print("   Password: admin123")
        print("\n⚠️  Remember to change the admin password!")
        print("\n🚀 Happy coding!")
    else:
        print("❌ SETUP FAILED")
        print("=" * 60)
        print("\n🔍 Troubleshooting:")
        print("   1. Check PostgreSQL is running:  sudo systemctl status postgresql")
        print("   2. Verify database exists:        psql -d postgres -c '\\l'")
        print("   3. Test connection:               python3 test_db_connection.py")
        print("   4. Check .env file:               python3 check_env.py")
        sys.exit(1)
    
    print("=" * 60)

if __name__ == '__main__':
    main()