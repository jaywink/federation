import importlib

from federation.exceptions import NoSuitableProtocolFoundError


PROTOCOLS = (
    "diaspora",
)


def handle_receive(payload, user=None):
    """Takes a payload and passes it to the correct protocol."""
    protocol = None
    for protocol_name in PROTOCOLS:
        protocol = importlib.import_module("federation.protocols.%s.protocol" % protocol_name)
        if protocol.identify_payload(payload):
            break

    if protocol:
        proto_obj = protocol.Protocol()
        return proto_obj.receive(payload, user)
    else:
        raise NoSuitableProtocolFoundError()
