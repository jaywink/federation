import importlib
import logging
from typing import Optional, Callable

from federation import identify_protocol_by_id
from federation.entities.base import Profile
from federation.protocols.activitypub import protocol as activitypub_protocol
from federation.protocols.diaspora import protocol as diaspora_protocol
from federation.utils.text import validate_handle

logger = logging.getLogger("federation")


def retrieve_remote_content(
        id: str, guid: str = None, handle: str = None, entity_type: str = None,
        sender_key_fetcher: Callable[[str], str] = None, cache: bool=True,
):
    """Retrieve remote content and return an Entity object.

    ``sender_key_fetcher`` is an optional function to use to fetch sender public key. If not given, network will be used
    to fetch the profile and the key. Function must take federation id as only parameter and return a public key.
    """
    if handle and validate_handle(handle):
        protocol_name = "diaspora"
        if not guid:
            guid = id
    else:
        protocol_name = identify_protocol_by_id(id).PROTOCOL_NAME
    utils = importlib.import_module("federation.utils.%s" % protocol_name)
    return utils.retrieve_and_parse_content(
        id=id, guid=guid, handle=handle, entity_type=entity_type, 
        cache=cache, sender_key_fetcher=sender_key_fetcher,
    )


def retrieve_remote_profile(id: str) -> Optional[Profile]:
    """High level retrieve profile method.

    Retrieve the profile from a remote location, using protocols based on the given ID.
    """
    if validate_handle(id):
        protocols = (activitypub_protocol, diaspora_protocol)
    else:
        protocols = (identify_protocol_by_id(id),)
    for protocol in protocols:
        utils = importlib.import_module(f"federation.utils.{protocol.PROTOCOL_NAME}")
        profile = utils.retrieve_and_parse_profile(id)
        if profile:
            return profile
