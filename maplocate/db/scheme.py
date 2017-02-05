import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

__all__ = ['user', 'roles']

meta = sa.MetaData()

user = sa.Table(
    "user", meta,
    sa.Column('id', sa.Integer, nullable=False),
    sa.Column('login', sa.String(64), nullable=False),
    sa.Column('password', sa.String(256), nullable=False),
    sa.Column('salt', sa.String(256), nullable=False),
    sa.Column('is_superuser', sa.Boolean, nullable=False,
              server_default='False'),
    sa.Column('firstname', sa.String(64), nullable=False),
    sa.Column('lastname', sa.String(64), nullable=False),
    sa.Column('disabled', sa.Boolean, nullable=False,
              server_default='False'),

    # indexes #
    sa.PrimaryKeyConstraint('id', name='user_pkey'),
    sa.UniqueConstraint('login', name='user_login_key'),
)

roles = sa.Table(
    'roles', meta,
    sa.Column('id', sa.Integer, nullable=False),
    sa.Column('role_name', sa.String(64), nullable=False),
    sa.Column('permissions', postgresql.ARRAY(sa.String(64))),
    sa.Column('description', sa.String(64), nullable=False,
              server_default=''),

    # indexes #
    sa.PrimaryKeyConstraint('id', name='roles_pkey'),
)

user_roles = sa.Table(
    'user_roles', meta,
    sa.Column('user_id', sa.Integer, nullable=False),
    sa.Column('role_id', sa.Integer, nullable=False),

    sa.PrimaryKeyConstraint('user_id', 'role_id', name='user_roles_pkey'),
    sa.ForeignKeyConstraint(['user_id'], [user.c.id],
                            name='user_roles_user_fkey',
                            ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['role_id'], [roles.c.id],
                            name='user_roles_role_fkey',
                            ondelete='RESTRICT'),
)
