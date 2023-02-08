import importlib
from types import ModuleType
from typing import Union, TYPE_CHECKING

from federation.exceptions import NoSuitableProtocolFoundError

if TYPE_CHECKING:
    from federation.types import RequestType

__version__ = "0.23.0"

PROTOCOLS = (
    "activitypub",
    "diaspora",
    "matrix",
)


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
