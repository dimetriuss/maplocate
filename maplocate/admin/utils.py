import logging
import random
import string
import hashlib
import asyncio
import json
import functools

from aiohttp import web
from datetime import datetime, timezone
from trafaret import DataError

from .exceptions import JsonBodyValidationError


log = logging.getLogger(__name__)


POPULATION = (string.ascii_letters + string.digits) * 10
RANDOM = random.SystemRandom()


def utc_now():
    return datetime.now(timezone.utc)


def generate_salt():
    salt = ''.join(RANDOM.sample(POPULATION, 256))
    return salt


def calculate_hash(password, salt):
    """Calculate hash based on password and salt."""
    hashid = hashlib.sha512()
    hashid.update(password.encode('utf8'))
    hashid.update(salt.encode('utf8'))
    password_hash = hashid.hexdigest()
    return password_hash


def validate_password(password, password_hash, salt):
    """Returns True if password equals hashed one."""
    return calculate_hash(password, salt) == password_hash


@asyncio.coroutine
def check_trafaret(traf, data, *, raise_error=True):
    """Applies trafaret to data and raises RESTError instead of DataError."""
    try:
        return traf(data)
    except DataError as err:
        if not raise_error:
            return None
        raise JsonBodyValidationError(fields=err.as_dict())


@asyncio.coroutine
def get_json_param(request, check_param, traf=None):
    try:
        json_data = yield from request.json()
    except ValueError:
        if check_param in request.GET:
            try:
                json_data = json.loads(request.GET[check_param])
            except ValueError:
                raise JsonBodyValidationError()
        else:
            if request.method != 'GET':
                raise JsonBodyValidationError()
            json_data = {}

    if traf:
        json_data = check_trafaret(traf, json_data)

    return json_data


def render_json(func):
    assert asyncio.iscoroutinefunction(func), func

    @asyncio.coroutine
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        ret = yield from func(*args, **kwargs)
        try:
            text = json.dumps(ret)
        except TypeError:
            raise RuntimeError("{!r} result {!r} is not serializable".format(
                func, ret))
        return web.Response(text=text, content_type='application/json')

    return wrapper


def validate(traf, *, as_param='form', as_kwargs=False, check_param=None):
    """Decorator for request.json() validation.
    Here is double coding for asyncio DEBUG mode, because in debug asyncio
    fails to wrap a coroutine twice."""
    def inner(func):

        if asyncio.iscoroutinefunction(func):
            @render_json
            @functools.wraps(func)
            @asyncio.coroutine
            def method_wrapper(self, request, *args, **kw):
                form = yield from get_json_param(request, check_param, traf)
                if as_kwargs:
                    kw.update(form)
                elif as_param:
                    kw[as_param] = form
                return (yield from func(self, request, *args, **kw))
        else:
            @render_json
            @functools.wraps(func)
            @asyncio.coroutine
            def method_wrapper(self, request, *args, **kw):
                form = yield from get_json_param(request, check_param, traf)
                if as_kwargs:
                    kw.update(form)
                elif as_param:
                    kw[as_param] = form
                return func(self, request, *args, **kw)
        return method_wrapper
    return inner


@asyncio.coroutine
def log_errors_middleware(app, handler):
    @asyncio.coroutine
    def middleware(request):
        try:
            return (yield from handler(request))
        except web.HTTPClientError as exc:
            # Log 400 errors
            body = yield from request.text()
            if not body and 'json_body' in request.GET:
                body = request.GET['json_body']
            log.error(
                "4XX error in maplocate REST: \n%s. \n"
                "Original request: \n%s %s (auth_token=%s) %s",
                exc.text, request.method, request.path,
                request.headers.get('Authorization'), body)
            raise
    return middleware
