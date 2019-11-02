import json
import logging
import xml
from typing import Callable
from urllib.parse import quote

from lxml import html
from xrd import XRD

from federation.inbound import handle_receive
from federation.types import RequestType
from federation.utils.network import fetch_document, try_retrieve_webfinger_document
from federation.utils.text import validate_handle

logger = logging.getLogger("federation")


def fetch_public_key(handle):
    """Fetch public key over the network.

    :param handle: Remote handle to retrieve public key for.
    :return: Public key in str format from parsed profile.
    """
    profile = retrieve_and_parse_profile(handle)
    return profile.public_key


def parse_diaspora_webfinger(document):
    """
    Parse Diaspora webfinger which is either in JSON format (new) or XRD (old).

    https://diaspora.github.io/diaspora_federation/discovery/webfinger.html
    """
    webfinger = {
        "hcard_url": None,
    }
    try:
        doc = json.loads(document)
        for link in doc["links"]:
            if link["rel"] == "http://microformats.org/profile/hcard":
                webfinger["hcard_url"] = link["href"]
                break
        else:
            logger.warning("parse_diaspora_webfinger: found JSON webfinger but it has no hcard href")
            raise ValueError
    except Exception:
        try:
            xrd = XRD.parse_xrd(document)
            webfinger["hcard_url"] = xrd.find_link(rels="http://microformats.org/profile/hcard").href
        except xml.parsers.expat.ExpatError:
            logger.warning("parse_diaspora_webfinger: found XML webfinger but it fails to parse (ExpatError)")
            pass
    return webfinger


def retrieve_diaspora_hcard(handle):
    """
    Retrieve a remote Diaspora hCard document.

    :arg handle: Remote handle to retrieve
    :return: str (HTML document)
    """
    webfinger = retrieve_and_parse_diaspora_webfinger(handle)
    document, code, exception = fetch_document(webfinger.get("hcard_url"))
    if exception:
        return None
    return document


def retrieve_and_parse_diaspora_webfinger(handle):
    """
    Retrieve a and parse a remote Diaspora webfinger document.

    :arg handle: Remote handle to retrieve
    :returns: dict
    """
    document = try_retrieve_webfinger_document(handle)
    if document:
        return parse_diaspora_webfinger(document)
    host = handle.split("@")[1]
    hostmeta = retrieve_diaspora_host_meta(host)
    if not hostmeta:
        return None
    url = hostmeta.find_link(rels="lrdd").template.replace("{uri}", quote(handle))
    document, code, exception = fetch_document(url)
    if exception:
        return None
    return parse_diaspora_webfinger(document)


def retrieve_diaspora_host_meta(host):
    """
    Retrieve a remote Diaspora host-meta document.

    :arg host: Host to retrieve from
    :returns: ``XRD`` instance
    """
    document, code, exception = fetch_document(host=host, path="/.well-known/host-meta")
    if exception:
        return None
    xrd = XRD.parse_xrd(document)
    return xrd


def _get_element_text_or_none(document, selector):
    """
    Using a CSS selector, get the element and return the text, or None if no element.

    :arg document: ``HTMLElement`` document
    :arg selector: CSS selector
    :returns: str or None
    """
    element = document.cssselect(selector)
    if element:
        return element[0].text
    return None


def _get_element_attr_or_none(document, selector, attribute):
    """
    Using a CSS selector, get the element and return the given attribute value, or None if no element.

    Args:
        document (HTMLElement) - HTMLElement document
        selector (str) - CSS selector
        attribute (str) - The attribute to get from the element
    """
    element = document.cssselect(selector)
    if element:
        return element[0].get(attribute)
    return None


def parse_profile_from_hcard(hcard: str, handle: str):
    """
    Parse all the fields we can from a hCard document to get a Profile.

    :arg hcard: HTML hcard document (str)
    :arg handle: User handle in username@domain.tld format
    :returns: ``federation.entities.diaspora.entities.DiasporaProfile`` instance
    """
    from federation.entities.diaspora.entities import DiasporaProfile  # Circulars
    doc = html.fromstring(hcard)
    profile = DiasporaProfile(
        name=_get_element_text_or_none(doc, ".fn"),
        image_urls={
            "small": _get_element_attr_or_none(doc, ".entity_photo_small .photo", "src"),
            "medium": _get_element_attr_or_none(doc, ".entity_photo_medium .photo", "src"),
            "large": _get_element_attr_or_none(doc, ".entity_photo .photo", "src"),
        },
        public=True,
        id=handle,
        handle=handle,
        guid=_get_element_text_or_none(doc, ".uid"),
        public_key=_get_element_text_or_none(doc, ".key"),
        username=handle.split('@')[0],
        _source_protocol="diaspora",
    )
    return profile


def retrieve_and_parse_content(
        id: str, guid: str, handle: str, entity_type: str, sender_key_fetcher: Callable[[str], str]=None,
):
    """Retrieve remote content and return an Entity class instance.

    This is basically the inverse of receiving an entity. Instead, we fetch it, then call "handle_receive".

    :param sender_key_fetcher: Function to use to fetch sender public key. If not given, network will be used
        to fetch the profile and the key. Function must take handle as only parameter and return a public key.
    :returns: Entity object instance or ``None``
    """
    if not validate_handle(handle):
        return
    _username, domain = handle.split("@")
    url = get_fetch_content_endpoint(domain, entity_type.lower(), guid)
    document, status_code, error = fetch_document(url)
    if status_code == 200:
        request = RequestType(body=document)
        _sender, _protocol, entities = handle_receive(request, sender_key_fetcher=sender_key_fetcher)
        if len(entities) > 1:
            logger.warning("retrieve_and_parse_content - more than one entity parsed from remote even though we"
                           "expected only one! ID %s", guid)
        if entities:
            return entities[0]
        return
    elif status_code == 404:
        logger.warning("retrieve_and_parse_content - remote content %s not found", guid)
        return
    if error:
        raise error
    raise Exception("retrieve_and_parse_content - unknown problem when fetching document: %s, %s, %s" % (
        document, status_code, error,
    ))


def retrieve_and_parse_profile(handle):
    """
    Retrieve the remote user and return a Profile object.

    :arg handle: User handle in username@domain.tld format
    :returns: ``federation.entities.Profile`` instance or None
    """
    hcard = retrieve_diaspora_hcard(handle)
    if not hcard:
        return None
    profile = parse_profile_from_hcard(hcard, handle)
    try:
        profile.validate()
    except ValueError as ex:
        logger.warning("retrieve_and_parse_profile - found profile %s but it didn't validate: %s",
                       profile, ex)
        return None
    return profile


def get_fetch_content_endpoint(domain, entity_type, guid):
    """Get remote fetch content endpoint.

    See: https://diaspora.github.io/diaspora_federation/federation/fetching.html
    """
    return "https://%s/fetch/%s/%s" % (domain, entity_type, guid)


def get_public_endpoint(id: str) -> str:
    """Get remote endpoint for delivering public payloads."""
    _username, domain = id.split("@")
    return "https://%s/receive/public" % domain


def get_private_endpoint(id: str, guid: str) -> str:
    """Get remote endpoint for delivering private payloads."""
    _username, domain = id.split("@")
    return "https://%s/receive/users/%s" % (domain, guid)
