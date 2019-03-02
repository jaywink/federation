import importlib

from federation.exceptions import NoSuitableProtocolFoundError

__version__ = "0.18.0-dev"

PROTOCOLS = (
    "activitypub",
    "diaspora",
)


def identify_protocol(method: str, value: str):
    """
    Loop through protocols, import the protocol module and try to identify the id or payload.
    """
    for protocol_name in PROTOCOLS:
        protocol = importlib.import_module(f"federation.protocols.{protocol_name}.protocol")
        if getattr(protocol, f"identify_{method}")(value):
            return protocol
    else:
        raise NoSuitableProtocolFoundError()


def identify_protocol_by_id(id: str):
    return identify_protocol('id', id)


def identify_protocol_by_payload(payload: str):
    return identify_protocol('payload', payload)
