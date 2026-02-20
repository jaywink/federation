import importlib
import logging
from typing import Optional, Callable

from federation import identify_protocol_by_id
from federation.entities.base import Profile
from federation.protocols.activitypub import protocol as activitypub_protocol
from federation.protocols.diaspora import protocol as diaspora_protocol
from federation.protocols.enums import ProtocolType
from federation.utils.text import validate_handle

logger = logging.getLogger("federation")


def retrieve_remote_content(
        id: str, guid: str = None, handle: str = None, entity_type: str = None,
        sender_key_fetcher: Callable[[str], str] = None, cache: bool=True,
        protocol: ProtocolType = None
):
    """Retrieve remote content and return an Entity object.

    ``sender_key_fetcher`` is an optional function to use to fetch sender public key. If not given, network will be used
    to fetch the profile and the key. Function must take federation id as only parameter and return a public key.
    """
    protocols = (ProtocolType.ACTIVITYPUB, ProtocolType.DIASPORA) if protocol == None else (protocol,)
    for protocol in protocols:
        utils = importlib.import_module(f"federation.utils.{protocol.string}")
        content = utils.retrieve_and_parse_content(
            id=id, guid=guid, handle=handle, entity_type=entity_type, 
            cache=cache, sender_key_fetcher=sender_key_fetcher,
        )
        if content: return content


def retrieve_remote_profile(id: str) -> Optional[Profile]:
    """High level retrieve profile method.

    Retrieve the profile from a remote location, using protocols based on the given ID.
    """
    protocols = (activitypub_protocol, diaspora_protocol)
    for protocol in protocols:
        utils = importlib.import_module(f"federation.utils.{protocol.PROTOCOL_NAME}")
        profile = utils.retrieve_and_parse_profile(id)
        if profile:
            return profile.merge_profiles()
