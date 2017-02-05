import asyncio
import json
import uuid
import time
import logging
import aioredis
import injections
import trafaret as t

from .exceptions import NoAccessTokenError, InvalidAccessTokenError


log = logging.getLogger(__name__)


@injections.has
class TokensManager:
    """Access tokens manager.
    Generate new token, store and get sessions from Redis.
    """

    redis = injections.depends(aioredis.RedisPool)

    ADMIN_TOKEN_PREFIX = 'tokens:admin:{token}'
    ADMIN_TTL = 86400 * 3  # 3 days
    ADMIN_INDEX_PREFIX = 'index:admin'

    admin_session = t.Dict({
        t.Key('uid'): t.Int[0:],
        t.Key('username'): t.String(max_length=64),
    })

    @staticmethod
    def make_access_token():
        return uuid.uuid4().hex

    def __init__(self, *, loop, timer=time):
        self._loop = loop
        # Used for last session operation monitoring.
        self.timer = timer

    @asyncio.coroutine
    def get_admin_session(self, request):
        """Returns admin session identified by access token."""

        token = self._get_token(request)
        return (yield from self._get_session(
            self.ADMIN_TOKEN_PREFIX.format(token=token),
            self.admin_session))

    @asyncio.coroutine
    def set_admin_session(self, token, session):
        """Stores admin session in Redis."""
        session = self.admin_session(session)
        yield from self._set_session(
            self.ADMIN_TOKEN_PREFIX.format(token=token),
            session, ttl=self.ADMIN_TTL)
        yield from self._index_session(
            self.ADMIN_INDEX_PREFIX, session['uid'], token, ttl=self.ADMIN_TTL)

    @asyncio.coroutine
    def invalidate_admin_session(self, uid):
        yield from self._invalidate_session(self.ADMIN_INDEX_PREFIX, uid,
                                            self.ADMIN_TOKEN_PREFIX)

    def _get_token(self, request):
        """Extracts AUTHORIZATION token from request header.
        Raises NoAccessTokenError if token not found in request header.
        """

        token = request.headers.get('AUTHORIZATION')
        if token is None:
            raise NoAccessTokenError()
        return token

    @asyncio.coroutine
    def _get_session(self, key, trafaret):
        """Get session data from Redis identified by key.
        Raises InvalidAccessTokenError if session data not found.
        """

        with (yield from self.redis) as conn:
            packed = yield from conn.get(key, encoding='utf-8')
        if not packed:
            raise InvalidAccessTokenError()
        try:
            data = json.loads(packed)
            return trafaret(data)
        except ValueError:
            log.warning("Bad data found in session: %r", packed, exc_info=True)
            raise InvalidAccessTokenError()

    @asyncio.coroutine
    def _set_session(self, key, value, *, ttl=0):
        """Packs and stores session data in Redis."""

        with (yield from self.redis) as conn:
            yield from conn.set(key, json.dumps(value), expire=ttl)

    @asyncio.coroutine
    def _index_session(self, index_key, uid, token, *, ttl=0):
        with (yield from self.redis) as conn:
            expires_on = self.timer.time()+ttl if ttl > 0 else float('inf')
            yield from conn.zadd(index_key, expires_on,
                                 "{}:{}".format(uid, token))

    @asyncio.coroutine
    def _invalidate_session(self, index_key, uid, token_format):

        with (yield from self.redis) as conn:
            values = []
            cursor = b'0'
            while cursor:
                # Return portions of sorted set and collect them in values
                cursor, buffer = yield from conn.zscan(
                    index_key, cursor, match="{}:*".format(uid))
                values.extend([val for val in buffer[::2]])

            for value in values:
                token = value[value.find(b':')+1:]
                yield from conn.delete(
                    token_format.format(token=token.decode('utf-8')))

            if values:
                yield from conn.zrem(index_key, *values)
