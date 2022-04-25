import logging

from requests_cache import install_cache, RedisCache, SQLiteCache


logger = logging.getLogger("federation")

# try to obtain redis config from django
try:
    from federation.utils.django import get_configuration
    cfg = get_configuration()
    if cfg.get('redis'):
        backend = RedisCache(namespace='fed_cache', **cfg['redis'])
    else:
        backend = SQLiteCache(db_path='fed_cache')
except ImportError:
    backend = SQLiteCache(db_path='fed_cache')

install_cache(backend=backend)
logger.info(f'requests_cache backend set to {type(backend).__name__}')
