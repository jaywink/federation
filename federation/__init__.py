import importlib
import logging
from types import ModuleType
from typing import Union, TYPE_CHECKING

from requests_cache import install_cache, RedisCache, SQLiteCache

from federation.exceptions import NoSuitableProtocolFoundError
from federation.utils.django import get_configuration

if TYPE_CHECKING:
    from federation.types import RequestType

__version__ = "0.22.0"

PROTOCOLS = (
    "activitypub",
    "diaspora",
    "matrix",
)

logger = logging.getLogger("federation")

# try to obtain redis config from django
cfg = get_configuration()
if cfg.get('redis'):
    backend = RedisCache(namespace='fed_cache', **cfg['redis'])
else:
    backend = SQLiteCache(db_path='fed_cache')
install_cache(backend=backend)
logger.info(f'requests_cache backend set to {type(backend).__name__}')


def identify_protocol(method, value):
    # type: (str, Union[str, RequestType]) -> ModuleType
    """
    Loop through protocols, import the protocol module and try to identify the id or request.
    """
    for protocol_name in PROTOCOLS:
        protocol = importlib.import_module(f"federation.protocols.{protocol_name}.protocol")
        if getattr(protocol, f"identify_{method}")(value):
            return protocol
    else:
        raise NoSuitableProtocolFoundError()


def identify_protocol_by_id(identifier: str) -> ModuleType:
    return identify_protocol('id', identifier)


def identify_protocol_by_request(request):
    # type: (RequestType) -> ModuleType
    return identify_protocol('request', request)
