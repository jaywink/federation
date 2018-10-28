import logging
from typing import Optional, Any

from federation.entities.activitypub.entities import ActivitypubProfile
from federation.entities.activitypub.mappers import message_to_objects
from federation.utils.network import fetch_document

logger = logging.getLogger('federation')


def retrieve_and_parse_document(id: str) -> Optional[Any]:
    """
    Retrieve remote document by ID and return the entity.
    """
    document, status_code, ex = fetch_document(id, extra_headers={'accept': 'application/activity+json'})
    if document:
        from federation.protocols.activitypub.protocol import Protocol
        protocol = Protocol()
        sender, payload = protocol.receive(document)
        entities = message_to_objects(payload, sender)
        if entities:
            return entities[0]


def retrieve_and_parse_profile(id: str) -> Optional[ActivitypubProfile]:
    """
    Retrieve the remote id and return a Profile object.
    """
    profile = retrieve_and_parse_document(id)
    if not profile:
        return
    try:
        profile.validate()
    except ValueError as ex:
        logger.warning("retrieve_and_parse_profile - found profile %s but it didn't validate: %s",
                       profile, ex)
        return
    return profile
