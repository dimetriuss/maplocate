"""create user, roles and user_roles tables

Revision ID: 6469a3ce275d
Revises:
Create Date: 2017-02-05 10:45:03.813399

"""
from alembic import op  # noqa
import sqlalchemy as sa  # noqa
from sqlalchemy.dialects import postgresql  # noqa


# revision identifiers, used by Alembic.
revision = '6469a3ce275d'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'user',
        sa.Column('id', sa.Integer, nullable=False),
        sa.Column('login', sa.String(64), nullable=False),
        sa.Column('password', sa.String(256), nullable=False),
        sa.Column('salt', sa.String(256), nullable=False),
        sa.Column('is_superuser', sa.Boolean, nullable=False,
                  server_default='FALSE'),
        sa.Column('firstname', sa.String(64), nullable=False),
        sa.Column('lastname', sa.String(64), nullable=False),
        sa.Column('disabled', sa.Boolean, nullable=False,
                  server_default='FALSE'),

        sa.PrimaryKeyConstraint('id', name='user_pkey'),
        sa.UniqueConstraint('login', name='user_login_key'),
    )

    op.create_table(
        "roles",
        sa.Column('id', sa.Integer, nullable=False),
        sa.Column('role_name', sa.String(64), nullable=False),
        sa.Column('permissions', postgresql.ARRAY(sa.String(64))),
        sa.Column('description', sa.String(64), nullable=False,
                  server_default=''),

        # indexes #
        sa.PrimaryKeyConstraint('id', name='roles_pkey'),
    )

    op.create_table(
        "user_roles",
        sa.Column('user_id', sa.Integer, nullable=False),
        sa.Column('role_id', sa.Integer, nullable=False),

        sa.PrimaryKeyConstraint('user_id', 'role_id', name='user_roles_pkey'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'],
                                name='user_roles_user_fkey',
                                ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'],
                                name='user_roles_role_fkey',
                                ondelete='RESTRICT'),
    )


def downgrade():
    op.drop_table('user_roles')
    op.drop_table('user')
    op.drop_table('roles')
