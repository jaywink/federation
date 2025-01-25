import json
import logging
import re
from typing import Optional, Any
from urllib.parse import urlparse

from federation.protocols.activitypub.signing import get_http_authentication
from federation.utils.network import fetch_document, try_retrieve_webfinger_document
from federation.utils.text import decode_if_bytes, validate_handle

logger = logging.getLogger('federation')

try:
    from federation.utils.django import get_federation_user
    federation_user = get_federation_user()
except Exception as exc:
    federation_user = None
    logger.warning("django is required for get requests signing: %s", exc)

type_path = re.compile(r'^application/(activity|ld)\+json')


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
        if link.get("rel") == "self" and type_path.match(link.get("type")):
            return link["href"]
    logger.debug("get_profile_id_from_webfinger: found webfinger but it has no as2 self href")


def get_profile_finger_from_webfinger(fid: str) -> Optional[str]:
    """
    Fetch remote webfinger subject acct (finger) using AS2 profile ID
    """
    document = try_retrieve_webfinger_document(fid)
    if not document:
        return

    try:
        doc = json.loads(document)
    except json.JSONDecodeError:
        return

    finger = doc.get('subject', '').replace('acct:', '')
    return finger if validate_handle(finger) else None


def retrieve_and_parse_content(**kwargs) -> Optional[Any]:
    return retrieve_and_parse_document(kwargs.get("id"), cache=kwargs.get('cache',True))


def retrieve_and_parse_document(fid: str, cache: bool=True) -> Optional[Any]:
    """
    Retrieve remote document by ID and return the entity.
    """
    from federation.entities.activitypub.models import element_to_objects # Circulars
    extra_headers={'accept': 'application/activity+json, application/ld+json; profile="https://www.w3.org/ns/activitystreams"'}
    auth=get_http_authentication(federation_user.rsa_private_key,
                                 f'{federation_user.id}#main-key',
                                 digest=False) if federation_user else None
    document, status_code, ex = fetch_document(fid,
                                               extra_headers=extra_headers,
                                               cache=cache,
                                               auth=auth)
    if document:
        try:
            document = json.loads(decode_if_bytes(document))
        except json.decoder.JSONDecodeError:
            return None
        entities = element_to_objects(document)
        if entities:
            entity = entities[0]
            id = entity.id or entity.activity_id
            # check against potential payload forgery (CVE-2024-23832)
            if urlparse(id).netloc != urlparse(fid).netloc:
                logger.warning('retrieve_and_parse_document - payload may be forged, discarding: %s', fid)
                return None
            logger.info("retrieve_and_parse_document - using first entity: %s", entity)
            return entity


def retrieve_and_parse_profile(fid: str) -> Optional[Any]:
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

