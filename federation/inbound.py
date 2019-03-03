import importlib
import logging
from typing import Tuple, List, Callable

from federation import identify_protocol_by_request
from federation.types import UserType, RequestType

logger = logging.getLogger("federation")


def handle_receive(
        request: RequestType,
        user: UserType = None,
        sender_key_fetcher: Callable[[str], str] = None,
        skip_author_verification: bool = False
) -> Tuple[str, str, List]:
    """Takes a request and passes it to the correct protocol.

    Returns a tuple of:
      - sender id
      - protocol name
      - list of entities

    NOTE! The returned sender is NOT necessarily the *author* of the entity. By sender here we're
    talking about the sender of the *request*. If this object is being relayed by the sender, the author
    could actually be a different identity.

    :arg request: Request object of type RequestType - note not a HTTP request even though the structure is similar
    :arg user: User that will be passed to `protocol.receive` (only required on private encrypted content)
        MUST have a `private_key` and `id` if given.
    :arg sender_key_fetcher: Function that accepts sender handle and returns public key (optional)
    :arg skip_author_verification: Don't verify sender (test purposes, false default)
    :returns: Tuple of sender id, protocol name and list of entity objects
    """
    logger.debug("handle_receive: processing request: %s", request)
    found_protocol = identify_protocol_by_request(request)

    logger.debug("handle_receive: using protocol %s", found_protocol.PROTOCOL_NAME)
    protocol = found_protocol.Protocol()
    sender, message = protocol.receive(
        request, user, sender_key_fetcher, skip_author_verification=skip_author_verification)
    logger.debug("handle_receive: sender %s, message %s", sender, message)

    mappers = importlib.import_module("federation.entities.%s.mappers" % found_protocol.PROTOCOL_NAME)
    entities = mappers.message_to_objects(message, sender, sender_key_fetcher, user)
    logger.debug("handle_receive: entities %s", entities)

    return sender, found_protocol.PROTOCOL_NAME, entities
