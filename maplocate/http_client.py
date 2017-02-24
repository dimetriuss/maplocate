import logging
import aiohttp
import asyncio
import json

log = logging.getLogger(__name__)


class HttpClientError(Exception):

    @property
    def status_code(self):
        return self.args[0]


class RestClient:

    def __init__(self, api_url, token=None, *, loop):
        self._api_url = api_url.rstrip('/')
        self.token = token
        self._loop = loop
        self.connector = aiohttp.TCPConnector(force_close=True, loop=loop)
        self.session = None

    @asyncio.coroutine
    def request(self, method, path, data=None, params=None, json_dumps=True):
        log.debug('API Request: %s %s;\nBODY: %r', method,
                  self._api_url + path, data)
        if json_dumps and (data is not None):
            data = json.dumps(data).encode('utf-8')
        if self.token is not None:
            headers = {'Authorization': self.token}
        else:
            headers = {}

        if self.session is None:
            self.session = aiohttp.ClientSession(connector=self.connector,
                                                 loop=self._loop)

        resp = yield from self.session.request(method,
                                               self._api_url + path,
                                               params=params,
                                               data=data,
                                               headers=headers)
        banswer = yield from resp.read()

        if 'text/plain' in resp.headers.get('content-type'):
            return banswer
        if resp.status in (200, 201):
            jsoned = yield from resp.json()
            return jsoned
        elif resp.status == 500:
            raise PlainRestError(banswer.decode('utf-8'))
        else:
            try:
                jsoned = yield from resp.json(encoding='utf-8')
            except ValueError:
                raise PlainRestError(banswer.decode('utf-8'))
            else:
                raise JsonRestError(resp.status, jsoned)

    def close(self):
        if self.session is not None:
            self.session.close()

    # Login API
    @asyncio.coroutine
    def login(self, login, password):
        path = '/auth/login'
        body = {'username': login, 'password': password}
        answer = yield from self.request("POST", path, body)
        self.token = answer['access_token']

    # Users API
    @asyncio.coroutine
    def user_create(self, login, password, firstname, lastname,
                    disabled=False):
        body = {'login': login,
                'password': password,
                'firstname': firstname,
                'lastname': lastname,
                'disabled': disabled}
        path = '/admin/users/'
        answer = yield from self.request("POST", path, body)
        return answer

    @asyncio.coroutine
    def user_details(self, uid):
        path = '/admin/users/{}'.format(uid)
        answer = yield from self.request("GET", path)
        return answer

    @asyncio.coroutine
    def user_update(self, uid, body):
        path = '/admin/users/{}'.format(uid)
        answer = yield from self.request("PATCH", path, body)
        return answer

    @asyncio.coroutine
    def user_delete(self, uid):
        path = '/admin/users/{}'.format(uid)
        answer = yield from self.request("DELETE", path)
        return answer

    @asyncio.coroutine
    def users_list(self, query=None):
        path = '/admin/users/'
        answer = yield from self.request("GET", path, data=query or {})
        return answer

    # Roles API
    @asyncio.coroutine
    def role_create(self, body):
        path = '/admin/roles/'
        answer = yield from self.request("POST", path, body)
        return answer

    @asyncio.coroutine
    def role_details(self, role_id):
        path = '/admin/roles/{role_id}'.format(role_id=role_id)
        return (yield from self.request('GET', path))

    @asyncio.coroutine
    def role_update(self, role_id, body, json_dumps=True):
        path = '/admin/roles/{role_id}'.format(role_id=role_id)
        return (yield from self.request(
            'PATCH', path, body, json_dumps=json_dumps))

    @asyncio.coroutine
    def role_delete(self, role_id):
        path = '/admin/roles/{role_id}'.format(role_id=role_id)
        return (yield from self.request('DELETE', path))

    @asyncio.coroutine
    def roles_list(self):
        path = '/admin/roles/'
        answer = yield from self.request("GET", path)
        return answer

    # Permissions API
    @asyncio.coroutine
    def permissions_list(self):
        path = '/admin/permissions'
        permissions = yield from self.request("GET", path)
        return permissions

    # Users roles API
    @asyncio.coroutine
    def get_user_roles(self, user):
        path = '/admin/users/{}/roles'.format(user)
        answer = yield from self.request("GET", path)
        return answer

    @asyncio.coroutine
    def update_user_roles(self, user, body):
        path = '/admin/users/{}/roles'.format(user)
        answer = yield from self.request("PUT", path, body)
        return answer


class RestClientError(Exception):
    """Base exception class for RESTClient"""

    @property
    def status_code(self):
        return self.args[0]


class PlainRestError(RestClientError):
    """Answer is not JSON, for example for 500 Internal Server Error"""

    @property
    def error_text(self):
        return self.args[1]


class JsonRestError(RestClientError):
    """Answer is JSON error report"""

    @property
    def error_json(self):
        return self.args[1]
