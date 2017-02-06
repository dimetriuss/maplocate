import asyncio
import injections

from maplocate import __version__

from .base import BaseHandler


@injections.has
class UsersHandler(BaseHandler):
    """Users and login handler."""

    @asyncio.coroutine
    def index(self, request):
        return {'APP_VERSION': __version__}

    @asyncio.coroutine
    def login(self):
        pass

    @asyncio.coroutine
    def user_create(self):
        pass

    @asyncio.coroutine
    def user_details(self):
        pass

    @asyncio.coroutine
    def user_update(self):
        pass

    @asyncio.coroutine
    def user_delete(self):
        pass

    @asyncio.coroutine
    def users_list(self):
        pass
