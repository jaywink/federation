import importlib
import logging
from typing import Tuple, List, Callable

from federation.exceptions import NoSuitableProtocolFoundError
from federation.types import UserType

logger = logging.getLogger("federation")

PROTOCOLS = (
    "activitypub",
    "diaspora",
)


def handle_receive(
        payload: str,
        user: UserType=None,
        sender_key_fetcher: Callable[[str], str]=None,
        skip_author_verification: bool=False
) -> Tuple[str, str, List]:
    """Takes a payload and passes it to the correct protocol.

    Returns a tuple of:
      - sender id
      - protocol name
      - list of entities

    NOTE! The returned sender is NOT necessarily the *author* of the entity. By sender here we're
    talking about the sender of the *payload*. If this object is being relayed by the sender, the author
    could actually be a different identity.

    :arg payload: Payload blob (str)
    :arg user: User that will be passed to `protocol.receive` (only required on private encrypted content)
        MUST have a `private_key` and `id` if given.
    :arg sender_key_fetcher: Function that accepts sender handle and returns public key (optional)
    :arg skip_author_verification: Don't verify sender (test purposes, false default)
    :returns: Tuple of sender id, protocol name and list of entity objects
    :raises NoSuitableProtocolFound: When no protocol was identified to pass message to
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
    entities = mappers.message_to_objects(message, sender, sender_key_fetcher, user)
    logger.debug("handle_receive: entities %s", entities)

    return sender, found_protocol.PROTOCOL_NAME, entities
