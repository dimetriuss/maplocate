"""Module holds user permissions"""
import enum
import aiopg.sa
import asyncio
import injections
import trafaret as t
from sqlalchemy import select, join

import maplocate.db.scheme as db
from .exceptions import PermissionDenied

__all__ = ['Permission', 'AuthenticationPolicy']


class _EnumDict(enum._EnumDict):

    def __setitem__(self, key, value):
        # Extend enum._EnumDict __setitem__() to have ability to save data as
        # {key: (key, value)} by overriding
        super().__setitem__(key, value)
        if key in self._member_names:
            dict.__setitem__(self, key, (key, value))


class _EnumMeta(enum.EnumMeta):

    @classmethod
    # Override Enum metaclass method __prepare__()
    def __prepare__(metacls, cls, bases):
        return _EnumDict()


class NamingEnum(enum.Enum, metaclass=_EnumMeta):
    """Auto naming enum.

    Hackish way to allow following enums:

    >>> class NameCopiesValueEnum(AutoNameEnum):
    ...     red = ()
    ...     green = ()
    >>> NameCopiesValueEnum.red
    <NameCopiesValueEnum.red: 'red'>
    >>> NameCopiesValueEnum.red.name
    'red'
    >>> NameCopiesValueEnum.red.value
    'red'
    >>> NameCopiesValueEnum('red')
    <NameCopiesValueEnum.red: 'red'>"""

    def __new__(cls, *args):
        name, *args = args
        obj = object.__new__(cls)
        obj._value_ = name
        obj._args = args
        return obj


class Permission(NamingEnum):
    """Permissions enum.
    Each value is auto-named (ie 'value' field is the same as 'name').
    Each value assigned is a permission description (used only in docs).
    """
    # Admin role actions
    roles_view = "View roles"
    roles_edit = "Edit roles"

    # Admin user actions
    users_view = "View other admin user's profile(s)"
    users_add = "Register admin user"
    users_edit = "Edit admin user profile"
    users_reset_password = "Reset user's password without confirmation"
    users_roles_edit = "Manage user's roles"

    @property
    def description(self):
        if self._args:
            return self._args[0]

    @classmethod
    def EnumTrafaret(cls):
        return t.Enum(*[p.value for p in cls])


@injections.has
class AuthenticationPolicy:
    """Class is used for user permissions checking"""

    postgres = injections.depends(aiopg.sa.Engine)

    def __init__(self):
        self._superuser_query = select([db.user.c.is_superuser])
        self._permission_query = select([db.roles]).select_from(
            join(db.roles, db.user_roles,
                 db.roles.c.id == db.user_roles.c.role_id))

    @asyncio.coroutine
    def is_superuser(self, user_id):
        with (yield from self.postgres) as conn:
            is_superuser = yield from conn.scalar(
                self._superuser_query.where(db.user.c.id == user_id))
            return is_superuser

    @asyncio.coroutine
    def check_permission(self, user_id, permission):
        """Check if user has required permission in any of his roles.
        Raises PermissionDenied if user has no requested permission.
        If user is a superuser - permissions are never checked.
        """
        permission = Permission(permission)
        with (yield from self.postgres) as conn:
            # check if user is superuser
            is_super = yield from conn.scalar(
                self._super_query.where(db.user.c.id == user_id))
            if is_super:
                return True

            rows = yield from conn.execute(
                self._permission_query
                .where(db.user_roles.c.user_id == user_id))
            for row in rows:
                if permission.name in set(row['permissions']):
                    break
            else:
                raise PermissionDenied(permission=permission.name)
            return True
