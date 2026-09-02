"""drop deprecated book content columns

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-09-02 00:00:00.000000

Book.content / Book.preview_content have been dead since the Mongo
migration (mongo_books.py) - verified all 19 books / 241 chapters are
present in MongoDB's book_pages collection before writing this. No code
reads or writes these columns anymore.
"""
from alembic import op
import sqlalchemy as sa


revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('books', 'content')
    op.drop_column('books', 'preview_content')


def downgrade():
    op.add_column('books', sa.Column('preview_content', sa.JSON(), nullable=True))
    op.add_column('books', sa.Column('content', sa.JSON(), nullable=True))
    # Note: downgrade recreates empty columns only - the original data is not
    # restored here. Re-run a reverse-migration from mongo_books.py's
    # book_pages collection if you ever actually need the data back.
