import logging
import logging.config
import yaml
import asyncio
import aiopg.sa
import aioredis

import trafaret as t


def init_logging(options):
    conf = options.log_config
    assert conf.exists(), (conf, "Does not exist")
    assert conf.suffix.lower() in {'.yaml', '.ini'}, conf
    with conf.open('rt') as f:
        if conf.suffix.lower() == '.yaml':
            logging.config.dictConfig(yaml.load(f))
        else:
            logging.config.fileConfig(f)


def load_config(config_file, config_trafaret):
    """Loads and verifies config file."""

    with config_file.open('rb') as f:
        data = yaml.load(f)
    return config_trafaret.check(data)


# Main config file trafaret with shortcuts

PostgresConf = t.Forward()
RedisConf = t.Forward()

maplocate_trafaret = t.Dict({
    t.Key('postgres'): PostgresConf,
    t.Key('redis'): RedisConf,
})


# trafaret shortcuts definition

PostgresConf << t.Dict({
    t.Key('database'): t.String,
    t.Key('user'): t.String,
    t.Key('password'): t.String,
    t.Key('host', default='127.0.0.1'): t.String,
    t.Key('port', default=5432): t.Int,
    t.Key('minsize', default=10): t.Int,
    t.Key('maxsize', default=10): t.Int,
    t.Key('connection_timeout', default=None): t.Int | t.Null,
})

RedisConf << t.Dict({
    t.Key('address'): t.Tuple(t.String, t.Int) | t.String,
    t.Key('db', default=1): t.Int[0:],
    t.Key('connection_timeout', default=None): t.Int | t.Null,
})

log = logging.getLogger(__name__)


@asyncio.coroutine
def init_postgres(inj, config, loop):
    log.info('Connecting to Postgres => %s:%s', config['host'], config['port'])
    try:
        fut = aiopg.sa.create_engine(
            database=config['database'],
            user=config['user'],
            password=config['password'],
            host=config['host'],
            port=config['port'],
            minsize=config['minsize'],
            maxsize=config['maxsize'],
            loop=loop)
        engine = yield from asyncio.wait_for(
            fut, timeout=config['connection_timeout'])
        inj['postgres'] = engine
    except asyncio.TimeoutError:
        log.error('Timeout connection to PostgreSQL')
        raise


@asyncio.coroutine
def init_redis(inj, config, loop):
    log.info('Connecting to Redis => %s', config['address'])
    try:
        fut = aioredis.create_pool(
            config['address'], db=config['db'], loop=loop)
        redis_pool = yield from asyncio.wait_for(
            fut, timeout=config['connection_timeout'])
        inj['redis'] = redis_pool
    except asyncio.TimeoutError:
        log.error('Timeout connection to Redis')
        raise
