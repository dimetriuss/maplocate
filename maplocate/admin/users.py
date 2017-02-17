import asyncio
import injections
import psycopg2
import itertools

import trafaret as t

from aiohttp_jinja2 import template
from sqlalchemy import select
from sqlalchemy.sql import or_

from maplocate.db import scheme as db
from maplocate import __version__
from .base import BaseHandler
from .utils import validate, generate_salt, calculate_hash
from .permissions import Permission
from .exceptions import (ObjectAlreadyExist, InvalidLogin, UserDisabled)


LoginUser = t.Dict({
    t.Key('username'): t.String(max_length=64),
    t.Key('password'): t.String(max_length=256),
})


CreateUserForm = t.Dict({
    t.Key('login'): t.Email,
    t.Key('password'): t.String(max_length=256),
    t.Key('disabled'): t.Bool(),
    t.Key('is_superuser', optional=True): t.Bool(),
    t.Key('firstname'): t.String(max_length=64),
    t.Key('lastname', default=''): t.String(max_length=64),
})


UserView = t.Dict({
    t.Key('id') >> 'uid': t.Int[0:],
    t.Key('login'): t.String,
    t.Key('firstname', default=''): t.String(allow_blank=True, max_length=64),
    t.Key('lastname', default=''): t.String(allow_blank=True, max_length=64),
    t.Key('roles', default=list): t.List(t.Dict({
        t.Key('id'): t.Int[0:],
        t.Key('role_name'): t.String,
        }).ignore_extra('*')),
    t.Key('disabled'): t.Bool(),
    t.Key('is_superuser'): t.Bool(),
}).ignore_extra('*')


FilterUserForm = t.Dict({
    t.Key("filter", default={}): t.Dict({
        t.Key("email", default=None, optional=True): t.String | t.Null,
        t.Key("fullname", default=None, optional=True): t.String | t.Null
    }),
})


@injections.has
class UsersHandler(BaseHandler):
    """Users and login handler."""

    @template('index.jinja2')
    @asyncio.coroutine
    def index(self, request):
        """Index page, needed for rendering basic html with app script.
        Request: 'GET', '/'
        """
        return {'APP_VERSION': __version__}

    @validate(LoginUser, as_kwargs=True)
    @asyncio.coroutine
    def login(self, request, username, password):
        """Verify user's credentials and return new access token and profile.
        Request: 'POST' '/auth/login'
        """

        with (yield from self.postgres) as pg_con:
            row = yield from pg_con.execute(
                db.user.select().where(db.user.c.login == username))
            rec = yield from row.first()
        if not rec:
            raise InvalidLogin()
        if rec.disabled:
            raise UserDisabled()

        pw_hash = calculate_hash(password, rec.salt)
        if pw_hash != rec.password:
            raise InvalidLogin()

        token = self.tokens.make_access_token()
        user = dict(rec)
        yield from self._add_roles(user)
        user = UserView(user)

        session = {'uid': rec.id, 'username': rec.login}

        yield from self.tokens.set_admin_session(token, session)
        return {'access_token': token, 'user': user}

    @validate(CreateUserForm)
    @asyncio.coroutine
    def user_create(self, request, form):
        """Create new user.
        Request: 'POST', '/admin/users'
        """

        user_row = {}
        session = yield from self.auth_admin_session(request,
                                                     Permission.users_add)
        with (yield from self.postgres) as pg_con:
            try:
                salt = generate_salt()
                password_hash = calculate_hash(form['password'], salt)
                form['password'] = password_hash
                form['salt'] = salt

                cursor = yield from pg_con.execute(db.user.insert()
                                                   .returning(*db.user.c)
                                                   .values(form))
                user_row = yield from cursor.first()
            except psycopg2.IntegrityError as err:
                if err.pgcode == db.PG_UNIQUE_VIOLATION:
                    raise ObjectAlreadyExist(
                        fields={'login': 'such user login already exists'})
                raise

        user = dict(user_row)
        yield from self._add_roles(user)

        yield from self.log_admin_action(request, session, form)

        return UserView(user)

    @asyncio.coroutine
    def user_details(self):
        pass

    @asyncio.coroutine
    def user_update(self):
        pass

    @asyncio.coroutine
    def user_delete(self):
        pass

    @validate(FilterUserForm, check_param='json_body')
    @asyncio.coroutine
    def users_list(self, request, form):
        """List users.
        Request: 'GET', 'admin/user/'
        """

        yield from self.auth_admin_session(request, Permission.user_view)
        with (yield from self.postgres) as pg_con:
            query = db.user.select()
            if form['filter']['fullname']:
                fname, *lname_tail = form['filter']['fullname'].split(' ')
                if lname_tail:
                    expr = or_(db.user.c.firstname.like(fname + '%'),
                               *[db.user.c.lastname.like(word + '%')
                                 for word in lname_tail])
                else:
                    expr = or_(db.user.c.firstname.like(fname + '%'),
                               db.user.c.lastname.like(fname + '%'))
                query = query.where(expr)

            if form['filter']['email']:
                query = query.where(
                    db.user.c.login.like(form['filter']['email'] + '%')
                )

            cursor = yield from pg_con.execute(
                query.order_by('firstname', 'lastname')
            )
            users = yield from cursor.fetchall()
            users = list(map(dict, users))
            yield from self._add_roles(users)

            return [UserView(user) for user in users]

    @asyncio.coroutine
    def _add_roles(self, user_or_users):
        if not isinstance(user_or_users, list):
            users = [user_or_users]
        else:
            users = user_or_users

        user_id_map = dict(((x['id'], x) for x in users))
        user_ids = list(user_id_map)

        with (yield from self.postgres) as conn:
            cursor = yield from conn.execute(
                select([db.user_roles.c.user_id,
                        db.roles.c.id,
                        db.roles.c.role_name])
                .select_from(db.roles.join(db.user_roles))
                .where(db.user_roles.c.user_id.in_(user_ids))
                .order_by(db.user_roles.c.user_id)
            )
            roles = yield from cursor.fetchall()
            for user_id, roles in itertools.groupby(
                    roles, key=lambda x: x.user_id):
                user_id_map[user_id]['roles'] = list(map(dict, roles))
