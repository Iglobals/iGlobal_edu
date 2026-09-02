"""add subscription tables

Revision ID: a1b2c3d4e5f6
Revises: f3a7c9e2b6d1
Create Date: 2026-08-31 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'f3a7c9e2b6d1'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('subscription_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('interval', sa.String(length=20), nullable=False),
        sa.Column('price_ngn', sa.Float(), nullable=False),
        sa.Column('price_usd', sa.Float(), nullable=True),
        sa.Column('paystack_plan_code', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
    )
    op.create_table('subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('paystack_customer_code', sa.String(length=100), nullable=True),
        sa.Column('paystack_subscription_code', sa.String(length=100), nullable=True),
        sa.Column('paystack_email_token', sa.String(length=255), nullable=True),
        sa.Column('current_period_end', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['plan_id'], ['subscription_plans.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )
    op.create_table('subscription_payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=True),
        sa.Column('provider', sa.String(length=20), nullable=True),
        sa.Column('provider_ref', sa.String(length=100), nullable=False),
        sa.Column('amount_ngn', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['plan_id'], ['subscription_plans.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider_ref'),
    )


def downgrade():
    op.drop_table('subscription_payments')
    op.drop_table('subscriptions')
    op.drop_table('subscription_plans')
