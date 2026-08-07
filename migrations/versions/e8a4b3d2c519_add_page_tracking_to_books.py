"""add page tracking to books

Revision ID: e8a4b3d2c519
Revises: d390cacc7f1b
Create Date: 2026-08-01 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'e8a4b3d2c519'
down_revision = 'd390cacc7f1b'
branch_labels = None
depends_on = None


def upgrade():
    # Add page_counts column (JSON array of page counts per chapter)
    op.add_column('books', sa.Column('page_counts', sa.JSON(), nullable=True))
    
    # Add total_pages column (sum of all pages across chapters)
    op.add_column('books', sa.Column('total_pages', sa.Integer(), nullable=True, server_default='0'))


def downgrade():
    # Remove the page tracking columns
    op.drop_column('books', 'total_pages')
    op.drop_column('books', 'page_counts')
