import json
import logging
import xml
from urllib.parse import quote

from lxml import html
from xrd import XRD

from federation.entities.base import Profile
from federation.inbound import handle_receive
from federation.utils.network import fetch_document

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
    try:
        host = handle.split("@")[1]
    except AttributeError:
        logger.warning("retrieve_and_parse_diaspora_webfinger: invalid handle given: %s", handle)
        return None
    document, code, exception = fetch_document(
        host=host, path="/.well-known/webfinger?resource=acct:%s" % quote(handle),
    )
    if document:
        return parse_diaspora_webfinger(document)
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


def parse_diaspora_uri(uri):
    """Parse Diaspora URI scheme string.

    See: https://diaspora.github.io/diaspora_federation/federation/diaspora_scheme.html

    :return: tuple of (handle, entity_type, guid) or ``None``.
    """
    if not uri.startswith("diaspora://"):
        return
    try:
        handle, entity_type, guid = uri.replace("diaspora://", "").rsplit("/", maxsplit=2)
    except ValueError:
        return
    return handle, entity_type, guid


def parse_profile_diaspora_id(id):
    """
    Parse profile handle and guid from diaspora ID.
    """
    handle, entity_type, guid = parse_diaspora_uri(id)
    if entity_type != "profile":
        raise ValueError(
            "Invalid entity type %s to generate private remote endpoint for delivery. Must be 'profile'." % entity_type
        )
    return handle, guid


def generate_diaspora_profile_id(handle, guid):
    """
    Generate a Diaspora profile ID from handle and guid.
    """
    return "diaspora://%s/profile/%s" % (handle, guid)


def parse_profile_from_hcard(hcard, handle):
    """
    Parse all the fields we can from a hCard document to get a Profile.

    :arg hcard: HTML hcard document (str)
    :arg handle: User handle in username@domain.tld format
    :returns: ``federation.entities.Profile`` instance
    """
    doc = html.fromstring(hcard)
    profile = Profile(
        name=_get_element_text_or_none(doc, ".fn"),
        image_urls={
            "small": _get_element_attr_or_none(doc, ".entity_photo_small .photo", "src"),
            "medium": _get_element_attr_or_none(doc, ".entity_photo_medium .photo", "src"),
            "large": _get_element_attr_or_none(doc, ".entity_photo .photo", "src"),
        },
        public=True if _get_element_text_or_none(doc, ".searchable") == "true" else False,
        handle=handle,
        guid=_get_element_text_or_none(doc, ".uid"),
        public_key=_get_element_text_or_none(doc, ".key"),
    )
    return profile


def retrieve_and_parse_content(id, sender_key_fetcher=None):
    """Retrieve remote content and return an Entity class instance.

    This is basically the inverse of receiving an entity. Instead, we fetch it, then call "handle_receive".

    :param id: Diaspora URI scheme format ID.
    :param sender_key_fetcher: Function to use to fetch sender public key. If not given, network will be used
        to fetch the profile and the key. Function must take handle as only parameter and return a public key.
    :returns: Entity object instance or ``None``
    """
    handle, entity_type, guid = parse_diaspora_uri(id)
    _username, domain = handle.split("@")
    url = get_fetch_content_endpoint(domain, entity_type, guid)
    document, status_code, error = fetch_document(url)
    if status_code == 200:
        _sender, _protocol, entities = handle_receive(document, sender_key_fetcher=sender_key_fetcher)
        if len(entities) > 1:
            logger.warning("retrieve_and_parse_content - more than one entity parsed from remote even though we"
                           "expected only one! ID %s", id)
        if entities:
            return entities[0]
        return
    elif status_code == 404:
        logger.warning("retrieve_and_parse_content - remote content %s not found", id)
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


def get_public_endpoint(id):
    """Get remote endpoint for delivering public payloads."""
    handle, _entity_type, _guid = parse_diaspora_uri(id)
    _username, domain = handle.split("@")
    return "https://%s/receive/public" % domain


def get_private_endpoint(id):
    """Get remote endpoint for delivering private payloads."""
    handle, guid = parse_profile_diaspora_id(id)
    _username, domain = handle.split("@")
    return "https://%s/receive/users/%s" % (domain, guid)
