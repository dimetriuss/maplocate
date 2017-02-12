import asyncio
import injections

from aiohttp_jinja2 import template

from maplocate import __version__
from .base import BaseHandler


@injections.has
class UsersHandler(BaseHandler):
    """Users and login handler."""

    @template('index.jinja2')
    @asyncio.coroutine
    def index(self, request):
        """Index page, needed for rendering basic html with app script."""
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
