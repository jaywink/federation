import json
import logging
from typing import Optional, Any

from federation.entities.activitypub.entities import ActivitypubProfile
from federation.protocols.activitypub.signing import get_http_authentication
from federation.utils.network import fetch_document, try_retrieve_webfinger_document
from federation.utils.text import decode_if_bytes, validate_handle

logger = logging.getLogger('federation')

try:
    from federation.utils.django import get_federation_user
    federation_user = get_federation_user()
except (ImportError, AttributeError):
    federation_user = None
    logger.warning("django is required for requests signing")

def get_profile_id_from_webfinger(handle: str) -> Optional[str]:
    """
    Fetch remote webfinger, if any, and try to parse an AS2 profile ID.
    """
    document = try_retrieve_webfinger_document(handle)
    if not document:
        return

    try:
        doc = json.loads(document)
    except json.JSONDecodeError:
        return
    for link in doc.get("links", []):
        if link.get("rel") == "self" and link.get("type") == "application/activity+json":
            return link["href"]
    logger.debug("get_profile_id_from_webfinger: found webfinger but it has no as2 self href")


def retrieve_and_parse_content(**kwargs) -> Optional[Any]:
    return retrieve_and_parse_document(kwargs.get("id"))


def retrieve_and_parse_document(fid: str) -> Optional[Any]:
    """
    Retrieve remote document by ID and return the entity.
    """
    from federation.entities.activitypub.models import element_to_objects # Circulars
    document, status_code, ex = fetch_document(fid, extra_headers={'accept': 'application/activity+json'}, 
            auth=get_http_authentication(federation_user.rsa_private_key,f'{federation_user.id}#main-key') if federation_user else None)
    if document:
        document = json.loads(decode_if_bytes(document))
        entities = element_to_objects(document)
        if entities:
            logger.info("retrieve_and_parse_document - using first entity: %s", entities[0])
            return entities[0]


def retrieve_and_parse_profile(fid: str) -> Optional[ActivitypubProfile]:
    """
    Retrieve the remote fid and return a Profile object.
    """
    if validate_handle(fid):
        profile_id = get_profile_id_from_webfinger(fid)
        if not profile_id:
            return
    else:
        profile_id = fid
    profile = retrieve_and_parse_document(profile_id)
    if not profile:
        return
    try:
        profile.validate()
    except ValueError as ex:
        logger.warning("retrieve_and_parse_profile - found profile %s but it didn't validate: %s",
                       profile, ex)
        return
    return profile

