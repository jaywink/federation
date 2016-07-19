import importlib

from federation.entities.diaspora.mappers import get_outbound_entity
from federation.exceptions import NoSuitableProtocolFoundError
from federation.protocols.diaspora.protocol import Protocol

PROTOCOLS = (
    "diaspora",
)


def handle_receive(payload, user=None, sender_key_fetcher=None, skip_author_verification=False):
    """Takes a payload and passes it to the correct protocol.

    Args:
        payload (str)                               - Payload blob
        user (optional, obj)                        - User that will be passed to `protocol.receive`
        sender_key_fetcher (optional, func)         - Function that accepts sender handle and returns public key
        skip_author_verification (optional, bool)   - Don't verify sender (test purposes, false default)
    """
    found_protocol = None
    for protocol_name in PROTOCOLS:
        protocol = importlib.import_module("federation.protocols.%s.protocol" % protocol_name)
        if protocol.identify_payload(payload):
            found_protocol = protocol
            break

    if found_protocol:
        protocol = found_protocol.Protocol()
        sender, message = protocol.receive(
            payload, user, sender_key_fetcher, skip_author_verification=skip_author_verification)
    else:
        raise NoSuitableProtocolFoundError()

    mappers = importlib.import_module("federation.entities.%s.mappers" % found_protocol.PROTOCOL_NAME)
    entities = mappers.message_to_objects(message)

    return sender, found_protocol.PROTOCOL_NAME, entities


def handle_create_payload(from_user, to_user, entity):
    """Create a payload with the correct protocol.

    Since we don't know the protocol, we need to first query the recipient. However, for a PoC implementation,
    supporting only Diaspora, we're going to assume that for now.

    Args:
        from_user (obj)     - User sending the object
        to_user (obj)       - Contact entry to send to
        entity (obj)        - Entity object to send

    `from_user` must have `private_key` and `handle` attributes.
    `to_user` must have `key` attribute.
    """
    # Just use Diaspora protocol for now
    protocol = Protocol()
    outbound_entity = get_outbound_entity(entity)
    data = protocol.build_send(from_user=from_user, to_user=to_user, entity=outbound_entity)
    return data
