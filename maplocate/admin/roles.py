import injections
import asyncio
import aiopg
import psycopg2
import trafaret as t

from sqlalchemy import select, join

from maplocate.db import scheme as db
from .base import BaseHandler
from .utils import validate, render_json
from .permissions import Permission
from .exceptions import (ObjectAlreadyExist,
                         ObjectNotFound,
                         JsonBodyValidationError)


Permissions = t.List(Permission.EnumTrafaret(), min_length=1)

CreateRoleForm = t.Dict({
    t.Key('role_name'): t.String(max_length=64),
    t.Key('permissions'): Permissions,
    t.Key('description', optional=True): t.String(max_length=64),
})

RoleView = t.Dict({
    t.Key('id'): t.Int[0:],
    t.Key('role_name'): t.String,
    t.Key('permissions'): Permissions,
    t.Key('description', default=''): t.String(allow_blank=True,
                                               max_length=64)
})

UpdateRoleForm = t.Dict({
    t.Key('role_name', optional=True): t.String(max_length=64),
    t.Key('permissions', optional=True): Permissions,
    t.Key('description', optional=True): t.String(max_length=64),
})

UpdateUserRolesForm = t.List(t.Int)


@injections.has
class RolesHandler(BaseHandler):
    """Roles and permissions handler."""

    postgres = injections.depends(aiopg.sa.Engine)

    PERMISSION_GROUPS = {
        'roles': 'Admin role actions',
        'users': 'Admin user actions'
    }

    @validate(CreateRoleForm)
    @asyncio.coroutine
    def role_create(self, request, form):
        """Create new role.
        Request: 'POST', '/admin/roles'
        """

        session = yield from self.auth_admin_session(request,
                                                     Permission.roles_edit)
        with (yield from self.postgres) as pg_con:
            transaction = yield from pg_con.begin()
            try:
                check_query = (
                    db.roles.select()
                    .where(db.roles.c.role_name == form['role_name']))
                row = yield from pg_con.scalar(check_query)
                if row is not None:
                    yield from transaction.rollback()
                    raise ObjectAlreadyExist(
                        fields={'role_name': 'role_name already exists'})

                cursor = yield from pg_con.execute(db.roles.insert()
                                                   .returning(*db.roles.c)
                                                   .values(form))
                yield from transaction.commit()
                row = yield from cursor.first()
            except psycopg2.IntegrityError:
                yield from transaction.rollback()
                raise

        yield from self.log_admin_action(request, session, form)

        return RoleView(dict(row))

    @render_json
    @asyncio.coroutine
    def role_details(self, request):
        """View role details.
        Request: 'GET', '/admin/roles/{role_id}'
        """

        yield from self.auth_admin_session(request, Permission.roles_view)
        role_id = self._get_role_id(request)
        with (yield from self.postgres) as pg_con:
            cursor = yield from pg_con.execute(
                db.roles.select()
                .where(db.roles.c.id == role_id))
            row = yield from cursor.first()
        return RoleView(dict(row))

    @validate(UpdateRoleForm)
    @asyncio.coroutine
    def role_update(self, request, form):
        """Update role.
        Request: 'PATCH', '/admin/roles/{role_id}'
        """

        session = yield from self.auth_admin_session(request,
                                                     Permission.roles_edit)
        role_id = self._get_role_id(request)
        updated_role = {}
        with (yield from self.postgres) as pg_con:
            try:
                cursor = yield from pg_con.execute(
                    select([db.roles])
                    .where(db.roles.c.id == role_id))

                old_role = yield from cursor.first()
                if not old_role:
                    raise ObjectNotFound()

                cursor = yield from pg_con.execute(
                    db.roles.update()
                    .returning(*db.roles.c)
                    .where(db.roles.c.id == role_id)
                    .values(form))

                updated_role = yield from cursor.first()
            except psycopg2.IntegrityError:
                raise JsonBodyValidationError()

        yield from self.log_admin_action(request, session, form)

        return RoleView(dict(updated_role))

    @render_json
    @asyncio.coroutine
    def role_delete(self, request):
        """Delete role if it is not assigned to anyone.
        Request: 'DELETE', '/admin/roles/{role_id}'
        """

        session = yield from self.auth_admin_session(request,
                                                     Permission.roles_edit)
        role_id = self._get_role_id(request)
        deleted_roles_amount = None

        with (yield from self.postgres) as pg_con:
            try:
                cursor = yield from pg_con.execute(
                    db.roles.delete()
                    .where(db.roles.c.id == role_id))
                deleted_roles_amount = cursor.rowcount
            except psycopg2.IntegrityError:
                raise JsonBodyValidationError()

        if not deleted_roles_amount:
            raise ObjectNotFound()
        assert deleted_roles_amount == 1

        yield from self.log_admin_action(request, session)

        return {'status': 'deleted'}

    @render_json
    @asyncio.coroutine
    def roles_list(self, request):
        """Get roles list.
        Request: 'GET', '/admin/roles/'
        """

        yield from self.auth_admin_session(request, Permission.roles_view)
        with (yield from self.postgres) as pg_con:
            result = yield from pg_con.execute(db.roles.select())
        return [RoleView(dict(row)) for row in result]

    @render_json
    @asyncio.coroutine
    def list_permissions(self):
        """List all system permissions.
        Request: 'GET', '/admin/permissions
        """

        grouped_permissions = []

        for perm in Permission:
            prefix, *tail = perm.value.split('_')
            group = self.PERMISSION_GROUPS.get(prefix, prefix.title())
            grouped_permissions.append((perm, group))

        return [
            {'id': perm.name, 'group': group, 'description': perm.description}
            for perm, group in grouped_permissions]

    @render_json
    @asyncio.coroutine
    def get_user_roles(self, request):
        """Get user roles.
        Request: 'GET', '/admin/users/{uid}/roles'
        """

        session = yield from self.tokens.get_admin_session(request)
        user_id = self.get_user_id(request)
        if session['uid'] != user_id:
            yield from self.auth_admin_session(request, Permission.users_view)
        user_roles = yield from self._get_user_roles(user_id)
        return [RoleView(dict(role)) for role in user_roles]

    @validate(UpdateUserRolesForm, as_param='lst')
    @asyncio.coroutine
    def update_user_roles(self, request, lst):
        """Update user roles.
        Request: 'PUT', '/admin/users/{uid}/roles'
        """

        session = yield from self.auth_admin_session(
            request, Permission.users_roles_edit)
        user_id = self.get_user_id(request)

        if len(lst) != len(set(lst)):
            raise JsonBodyValidationError(fields={
                'roles': 'Duplicates in user roles list'
            })

        with (yield from self.postgres) as pg_con:
            transaction = yield from pg_con.begin()
            try:
                yield from pg_con.execute(
                    """
                    CREATE TEMP TABLE user_roles_temp (
                    LIKE user_roles INCLUDING DEFAULTS
                    INCLUDING CONSTRAINTS
                    INCLUDING INDEXES)
                    """)

                user_roles_list = ','.join(
                    '({}, {})'.format(user_id, _) for _ in lst)
                if user_roles_list:
                    yield from pg_con.execute(
                        """
                        INSERT INTO user_roles_temp (user_id, role_id)
                        VALUES {};
                        """.format(user_roles_list))

                result = yield from pg_con.execute(
                    """
                    SELECT * FROM roles WHERE id IN
                    (SELECT role_id FROM user_roles_temp WHERE
                                        user_id={userid})
                    """.format(userid=user_id))

                if result.rowcount != len(lst):
                    yield from transaction.rollback()
                    valid_ids = [rec.id for rec in result.fetchall()]
                    invalid_ids = list(set(lst) - set(valid_ids))
                    raise JsonBodyValidationError(fields={
                        'roles': "Received invalid ids: {}".format(
                            invalid_ids
                        )
                    })

                where_non_actual_roles = """
                    WHERE ur.user_id={userid} AND
                    r.id = ur.role_id AND
                    ur.role_id NOT IN
                    (SELECT role_id FROM user_roles_temp WHERE
                    user_id={userid})
                    """.format(userid=user_id)

                # drop non actual roles
                yield from pg_con.execute("""
                    DELETE FROM user_roles as ur USING roles as r
                    """ + where_non_actual_roles)

                # drop already in list roles
                yield from pg_con.execute(
                    """
                    DELETE FROM user_roles_temp as t USING user_roles as ur
                    WHERE t.user_id = ur.user_id AND ur.role_id = t.role_id
                    """)

                # insert roles
                yield from pg_con.execute(
                    """
                    INSERT INTO user_roles (user_id, role_id)
                    SELECT user_id, role_id
                    FROM user_roles_temp
                    """)

                yield from pg_con.execute("DROP TABLE user_roles_temp;")

            except psycopg2.IntegrityError:
                yield from transaction.rollback()
                raise JsonBodyValidationError()
            else:
                yield from transaction.commit()
        roles = yield from self._get_user_roles(user_id)

        yield from self.log_admin_action(request, session, lst)

        return [RoleView(dict(rec)) for rec in roles]

    def _get_role_id(self, request):
        return self.matchdict_get(request, 'role_id')

    @asyncio.coroutine
    def _get_user_roles(self, user_id):
        perm_query = select([db.roles]).select_from(
            join(db.roles, db.user_roles,
                 db.roles.c.id == db.user_roles.c.role_id))

        with (yield from self.postgres) as pg_con:
            user_roles = yield from pg_con.execute(
                perm_query.where(db.user_roles.c.user_id == user_id))
        return user_roles
