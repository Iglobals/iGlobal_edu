"""add JUPEB exam-access packages (book exam keys/add-on price, purchase
package + iTest grant tracking, exam_access_purchases upgrade table)

Revision ID: c4e7a9b1d2f3
Revises: b2c3d4e5f6a7
Create Date: 2026-10-21 00:00:00.000000

Backfills books.exam_keys / exam_addon_price_naira from the title:
  "JUPEB KEYPOINTS FOR <SUBJECT>"      -> [key], 1000
  "THREE-IN-ONE ... (A, B, C)"         -> [kA, kB, kC], 2000
Everything else is left with no package. The mapping below is an inline COPY
of exam_packages.py (migrations must not import live app code) - keep them
in sync.
"""
import re

from alembic import op
import sqlalchemy as sa


revision = 'c4e7a9b1d2f3'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


# ── inline copy of exam_packages.py (frozen at this revision) ─────────────
_SUBJECT_ALIASES = {
    'mathematics': 'jupeb-mathematics',
    'maths': 'jupeb-mathematics',
    'math': 'jupeb-mathematics',
    'physics': 'jupeb-physics',
    'biology': 'jupeb-biology',
    'chemistry': 'jupeb-chemistry',
    'government': 'jupeb-government',
    'literature': 'jupeb-literature-in-english',
    'literature in english': 'jupeb-literature-in-english',
    'economics': 'jupeb-economics',
    'crs': 'jupeb-crs',
    'christian religious studies': 'jupeb-crs',
    'accounting': 'jupeb-accounting',
    'business': 'jupeb-business-studies',
    'business studies': 'jupeb-business-studies',
}
_SINGLE_RE = re.compile(r'^\s*JUPEB\s+KEYPOINTS\s+FOR\s+(.+?)\s*$', re.IGNORECASE)
_THREE_IN_ONE_RE = re.compile(r'^\s*THREE-IN-ONE\b.*\(([^)]*)\)', re.IGNORECASE)


def _subject_to_key(name):
    return _SUBJECT_ALIASES.get(' '.join((name or '').replace('-', ' ').lower().split()))


def parse_title_exam_package(title):
    title = title or ''
    m = _THREE_IN_ONE_RE.match(title)
    if m:
        parts = [p.strip() for p in m.group(1).split(',') if p.strip()]
        keys = [_subject_to_key(p) for p in parts]
        if not keys or any(k is None for k in keys):
            return [], None
        return list(dict.fromkeys(keys)), 2000.0
    m = _SINGLE_RE.match(title)
    if m:
        key = _subject_to_key(m.group(1))
        if key:
            return [key], 1000.0
    return [], None
# ───────────────────────────────────────────────────────────────────────────


def upgrade():
    op.add_column('books', sa.Column('exam_keys', sa.JSON(), nullable=True))
    op.add_column('books', sa.Column('exam_addon_price_naira', sa.Float(), nullable=True))

    op.add_column('purchases', sa.Column('package', sa.String(length=20), nullable=False, server_default='book'))
    op.add_column('purchases', sa.Column('exam_access_granted_at', sa.DateTime(), nullable=True))
    op.add_column('purchases', sa.Column('exam_access_last_error', sa.Text(), nullable=True))

    op.create_table(
        'exam_access_purchases',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('book_id', sa.Integer(), sa.ForeignKey('books.id', ondelete='CASCADE'), nullable=False),
        sa.Column('amount_paid', sa.Float(), nullable=False),
        sa.Column('payment_reference', sa.String(length=100), nullable=True, unique=True),
        sa.Column('payment_status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('exam_access_granted_at', sa.DateTime(), nullable=True),
        sa.Column('exam_access_last_error', sa.Text(), nullable=True),
        sa.UniqueConstraint('user_id', 'book_id', name='unique_exam_access_purchase'),
    )

    # Backfill existing books from their titles.
    books = sa.table(
        'books',
        sa.column('id', sa.Integer),
        sa.column('title', sa.String),
        sa.column('exam_keys', sa.JSON),
        sa.column('exam_addon_price_naira', sa.Float),
    )
    bind = op.get_bind()
    rows = bind.execute(sa.select(books.c.id, books.c.title)).fetchall()
    for book_id, title in rows:
        keys, addon = parse_title_exam_package(title)
        bind.execute(
            books.update().where(books.c.id == book_id)
            .values(exam_keys=keys, exam_addon_price_naira=addon)
        )


def downgrade():
    op.drop_table('exam_access_purchases')
    op.drop_column('purchases', 'exam_access_last_error')
    op.drop_column('purchases', 'exam_access_granted_at')
    op.drop_column('purchases', 'package')
    op.drop_column('books', 'exam_addon_price_naira')
    op.drop_column('books', 'exam_keys')
