import asyncio
import aiopg
import injections
import logging
import trafaret as t

from maplocate.admin.permissions import AuthenticationPolicy
from maplocate.admin.tokens import TokensManager
from .exceptions import ObjectNotFound, PermissionDenied


actions_log = logging.getLogger('maplocate.admin.actions_log')


@injections.has
class BaseHandler:

    permissions = injections.depends(AuthenticationPolicy)
    tokens = injections.depends(TokensManager)
    postgres = injections.depends(aiopg.sa.Engine)

    def __init__(self, loop):
        self._loop = loop

    @asyncio.coroutine
    def auth_superadmin_session(self, request):
        """Check super admin session and return it.
        In case of missing token NoAccessTokenError will be raised.
        In case of the invalid token InvalidAccessTokenError will be raised.
        """

        session = yield from self.tokens.get_admin_session(request)
        is_superuser = yield from self.permissions.is_superuser(session['uid'])
        if not is_superuser:
            raise PermissionDenied(reason='Must be superadmin')
        return session

    @asyncio.coroutine
    def auth_admin_session(self, request, permission):
        """Check specified permission for admin session and return it.
        In case of missing token NoAccessTokenError will be raised.
        In case of the invalid token InvalidAccessTokenError will be raised.
        If permission is not granted than PermissionDenied will be raised.
        """

        session = yield from self.tokens.get_admin_session(request)
        user_id = session['uid']
        yield from self.permissions.check_permission(user_id, permission)
        return session

    @asyncio.coroutine
    def log_admin_action(self, request, session, form=""):
        actions_log.info(
            "Admin action: %s %s (UID=%s, email=%s) %r",
            request.method, request.path, session['uid'],
            session['username'], form)

    def matchdict_get(self, request, key, traf=t.Int[1:]):
        """Extract info from request route."""

        assert not isinstance(traf, type), ("Use trafaret instance", traf)
        value = request.match_info.get(key)
        assert value is not None, "{!r} not found in {!r}".format(
            key, request.match_info)
        try:
            return traf(value)
        except t.DataError:
            raise ObjectNotFound()
