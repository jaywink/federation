import json
import logging
from typing import Optional, Any

from federation.entities.activitypub.entities import ActivitypubProfile
from federation.entities.activitypub.mappers import message_to_objects
from federation.utils.network import fetch_document
from federation.utils.text import decode_if_bytes

logger = logging.getLogger('federation')


def retrieve_and_parse_document(fid: str) -> Optional[Any]:
    """
    Retrieve remote document by ID and return the entity.
    """
    document, status_code, ex = fetch_document(fid, extra_headers={'accept': 'application/activity+json'})
    if document:
        document = json.loads(decode_if_bytes(document))
        entities = message_to_objects(document, fid)
        if entities:
            return entities[0]


def retrieve_and_parse_profile(fid: str) -> Optional[ActivitypubProfile]:
    """
    Retrieve the remote fid and return a Profile object.
    """
    profile = retrieve_and_parse_document(fid)
    if not profile:
        return
    try:
        profile.validate()
    except ValueError as ex:
        logger.warning("retrieve_and_parse_profile - found profile %s but it didn't validate: %s",
                       profile, ex)
        return
    return profile
