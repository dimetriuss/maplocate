import injections
import asyncio
import aiopg
import psycopg2
import trafaret as t

from sqlalchemy import select

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


@injections.has
class RolesHandler(BaseHandler):
    """Roles and permissions handler."""

    postgres = injections.depends(aiopg.sa.Engine)

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

    @asyncio.coroutine
    def role_delete(self):
        pass

    @asyncio.coroutine
    def roles_list(self):
        pass

    @asyncio.coroutine
    def list_permissions(self):
        pass

    @asyncio.coroutine
    def get_user_roles(self):
        pass

    @asyncio.coroutine
    def update_user_roles(self):
        pass

    def _get_role_id(self, request):
        return self.matchdict_get(request, 'role_id')
