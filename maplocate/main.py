import logging
import pathlib
import asyncio
import injections
import aiohttp_jinja2
import jinja2
import argsrun

from aiohttp import web

from maplocate.config import (init_logging, load_config, maplocate_trafaret,
                              init_postgres, init_redis)
from maplocate.admin.utils import log_errors_middleware
from maplocate.admin.users import UsersHandler
from maplocate.admin.roles import RolesHandler
from maplocate.admin.tokens import TokensManager
from maplocate.admin.permissions import AuthenticationPolicy
from maplocate.admin.routes import setup_routes as setup_maplocate_routes

log = logging.getLogger(__name__)

PROJECT_ROOT = pathlib.Path(__file__).parent.parent

TEMPLATES_ROOT = pathlib.Path(__file__).parent / 'templates'


def setup_maplocate_parser(ap):
    ap.add_argument('--config',
                    default=PROJECT_ROOT / 'config/maplocate.yaml',
                    type=pathlib.Path,
                    help='Configuration file, default `%(default)`')
    ap.add_argument('--host',
                    default='localhost',
                    help='Hostname or IP-address to bind to'
                         ' (default `%(default)`)')
    ap.add_argument('--port',
                    default=8081,
                    help='Port to bind to (default `%(default)`)')
    ap.add_argument('--unix-socket',
                    help='Path to unix socket to be used as transport. '
                         '`--host` and `--port` are ignored if passed')
    ap.add_argument('--log-config',
                    default=PROJECT_ROOT / 'config/logging.yaml',
                    type=pathlib.Path,
                    help='Logging config file path, default `%(default)`')


def maplocate_handler(options):
    """Running maplocate site"""

    init_logging(options)
    config = load_config(options.config, maplocate_trafaret)

    loop = asyncio.get_event_loop()

    app = web.Application(middlewares=[log_errors_middleware], loop=loop)
    inj = injections.Container()

    users_handler = UsersHandler(loop=loop)
    roles_handler = RolesHandler(loop=loop)

    aiohttp_jinja2.setup(
        app, loader=jinja2.FileSystemLoader(str(TEMPLATES_ROOT))
    )

    app.router.add_static('/static/', path=str(PROJECT_ROOT / 'static'))
    setup_maplocate_routes(app, users_handler, roles_handler)

    @asyncio.coroutine
    def init():
        # Setup dependencies
        yield from init_postgres(inj, config['postgres'], loop)
        yield from init_redis(inj, config['redis'], loop)
        tokens = TokensManager(loop=loop)
        permissions = AuthenticationPolicy()

        # Inject dependencies
        inj['tokens'] = tokens
        inj['permissions'] = permissions
        inj.inject(tokens)
        inj.inject(permissions)
        inj.inject(users_handler)
        inj.inject(roles_handler)

        handler = app.make_handler()

        if not options.unix_socket:
            log.info('Starting maplocate server => %s:%s',
                     options.host, options.port)

            srv = yield from loop.create_server(handler,
                                                options.host,
                                                options.port)
        else:
            log.info('Starting maplocate server on unix socket => %s',
                     options.unix_socket)

            srv = yield from loop.create_unix_server(
                handler, path=options.unix_socket)

        return srv, handler

    run = loop.run_until_complete
    srv, handler = run(init())
    try:
        log.info("Maplocate service is started")
        loop.run_forever()
    except KeyboardInterrupt:
        log.info("shutting down...")
        srv.close()
        run(srv.wait_closed())
        run(app.shutdown())
        run(handler.shutdown(timeout=20.0))
        run(app.cleanup())
        run(inj['redis'].clear())
        inj['postgres'].close()
        run(inj['postgres'].wait_closed())
        loop.close()
        log.info("Maplocate service is stopped")

admin_maplocate = argsrun.Entry(maplocate_handler, setup_maplocate_parser)
