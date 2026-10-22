"""add institutional agents

Revision ID: inst_agents_001
Revises: 
Create Date: 2026-10-22

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'inst_agents_001'
down_revision = None  # Update this to your latest migration
branch_labels = None
depends_on = None


def upgrade():
    # Add agent_type column to referral_agents
    with op.batch_alter_table('referral_agents', schema=None) as batch_op:
        batch_op.add_column(sa.Column('agent_type', sa.String(20), nullable=False, server_default='regular'))
    
    # Add buyer relationship to referral_commissions for easy querying
    # (buyer_id FK already exists, just need the backref in models)


def downgrade():
    with op.batch_alter_table('referral_agents', schema=None) as batch_op:
        batch_op.drop_column('agent_type')
