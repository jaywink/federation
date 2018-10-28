import importlib
import logging
from typing import Optional, Callable

from federation.entities.base import Profile

logger = logging.getLogger("federation")


def retrieve_remote_content(
        id: str, guid: str=None, handle: str=None, entity_type: str=None, sender_key_fetcher: Callable[[str], str]=None,
):
    """Retrieve remote content and return an Entity object.

    Currently, due to no other protocols supported, always use the Diaspora protocol.

    :param sender_key_fetcher: Function to use to fetch sender public key. If not given, network will be used
        to fetch the profile and the key. Function must take handle as only parameter and return a public key.
    :returns: Entity class instance or ``None``
    """
    # TODO add support for AP
    protocol_name = "diaspora"
    if not guid:
        guid = id
    utils = importlib.import_module("federation.utils.%s" % protocol_name)
    return utils.retrieve_and_parse_content(
        guid=guid, handle=handle, entity_type=entity_type, sender_key_fetcher=sender_key_fetcher,
    )


def retrieve_remote_profile(id: str) -> Optional[Profile]:
    """High level retrieve profile method.

    Retrieve the profile from a remote location, using protocol based on the given ID.
    """
    protocol_name = "diaspora"
    utils = importlib.import_module("federation.utils.%s" % protocol_name)
    return utils.retrieve_and_parse_profile(id.lower())
