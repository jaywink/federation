import importlib
from typing import Union, TYPE_CHECKING, Any

from federation.exceptions import NoSuitableProtocolFoundError

if TYPE_CHECKING:
    from federation.types import RequestType

__version__ = "0.18.0"

PROTOCOLS = (
    "activitypub",
    "diaspora",
)


def identify_protocol(method, value):
    # type: (str, Union[str, RequestType]) -> str
    """
    Loop through protocols, import the protocol module and try to identify the id or request.
    """
    for protocol_name in PROTOCOLS:
        protocol = importlib.import_module(f"federation.protocols.{protocol_name}.protocol")
        if getattr(protocol, f"identify_{method}")(value):
            return protocol
    else:
        raise NoSuitableProtocolFoundError()


def identify_protocol_by_id(id: str):
    return identify_protocol('id', id)


def identify_protocol_by_request(request):
    # type: (RequestType) -> Any
    return identify_protocol('request', request)
