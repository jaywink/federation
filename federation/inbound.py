import importlib
import logging

from federation.exceptions import NoSuitableProtocolFoundError

logger = logging.getLogger("social-federation")

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
    logger.debug("handle_receive: processing payload: %s", payload)
    found_protocol = None
    for protocol_name in PROTOCOLS:
        protocol = importlib.import_module("federation.protocols.%s.protocol" % protocol_name)
        if protocol.identify_payload(payload):
            found_protocol = protocol
            break

    if found_protocol:
        logger.debug("handle_receive: using protocol %s", found_protocol.PROTOCOL_NAME)
        protocol = found_protocol.Protocol()
        sender, message = protocol.receive(
            payload, user, sender_key_fetcher, skip_author_verification=skip_author_verification)
        logger.debug("handle_receive: sender %s, message %s", sender, message)
    else:
        raise NoSuitableProtocolFoundError()

    mappers = importlib.import_module("federation.entities.%s.mappers" % found_protocol.PROTOCOL_NAME)
    entities = mappers.message_to_objects(message)
    logger.debug("handle_receive: entities %s", entities)

    return sender, found_protocol.PROTOCOL_NAME, entities
