import injections
import asyncio

from .base import BaseHandler


@injections.has
class RolesHandler(BaseHandler):
    """Roles and permissions handler."""

    @asyncio.coroutine
    def role_create(self):
        pass

    @asyncio.coroutine
    def role_details(self):
        pass

    @asyncio.coroutine
    def role_update(self):
        pass

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
