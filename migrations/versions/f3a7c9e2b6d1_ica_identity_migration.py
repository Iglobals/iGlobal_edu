"""ica identity migration

Revision ID: f3a7c9e2b6d1
Revises: e8a4b3d2c519
Create Date: 2026-08-07 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f3a7c9e2b6d1'
down_revision = 'e8a4b3d2c519'
branch_labels = None
depends_on = None


def upgrade():
    # ── users: identify by iGlobals Central Auth instead of a local password ──
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('ica_sub', sa.String(length=255), nullable=True))
        batch_op.create_unique_constraint('uq_users_ica_sub', ['ica_sub'])
        batch_op.drop_column('password_hash')
        batch_op.drop_column('session_token')
        batch_op.drop_column('locked_ip')

    # otp_codes only ever backed the native forgot-password flow, which is gone
    op.drop_table('otp_codes')

    # ── referral_agents: agent is now a role on a normal ICA user, not its own login ──
    with op.batch_alter_table('referral_agents', schema=None) as batch_op:
        # Nullable for now — existing agent rows are linked to their ICA identity
        # the next time that agent logs in (see auth_routes.sync_agent_profile).
        # A follow-up migration can tighten this to NOT NULL once every existing
        # agent has logged in at least once post-cutover.
        batch_op.add_column(sa.Column('user_id', sa.Integer(), nullable=True))
        batch_op.create_unique_constraint('uq_referral_agents_user_id', ['user_id'])
        batch_op.create_foreign_key('fk_referral_agents_user_id', 'users', ['user_id'], ['id'], ondelete='CASCADE')
        batch_op.drop_column('username')
        batch_op.drop_column('password_hash')


def downgrade():
    with op.batch_alter_table('referral_agents', schema=None) as batch_op:
        batch_op.add_column(sa.Column('password_hash', sa.String(length=255), nullable=False, server_default=''))
        batch_op.add_column(sa.Column('username', sa.String(length=50), nullable=False, server_default=''))
        batch_op.drop_constraint('fk_referral_agents_user_id', type_='foreignkey')
        batch_op.drop_constraint('uq_referral_agents_user_id', type_='unique')
        batch_op.drop_column('user_id')

    op.create_table('otp_codes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=6), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('used', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('locked_ip', sa.String(length=45), nullable=True))
        batch_op.add_column(sa.Column('session_token', sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column('password_hash', sa.String(length=255), nullable=False, server_default=''))
        batch_op.drop_constraint('uq_users_ica_sub', type_='unique')
        batch_op.drop_column('ica_sub')
