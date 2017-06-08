# -*- coding: utf-8 -*-
import logging
import xml
from urllib.parse import quote

from lxml import html
from xrd import XRD

from federation.entities.base import Profile
from federation.utils.network import fetch_document

logger = logging.getLogger("federation")


def retrieve_diaspora_hcard(handle):
    """
    Retrieve a remote Diaspora hCard document.

    :arg handle: Remote handle to retrieve
    :return: str (HTML document)
    """
    webfinger = retrieve_diaspora_webfinger(handle)
    if not webfinger:
        return None
    url = webfinger.find_link(rels="http://microformats.org/profile/hcard").href
    document, code, exception = fetch_document(url)
    if exception:
        return None
    return document


def retrieve_diaspora_webfinger(handle):
    """
    Retrieve a remote Diaspora webfinger document.

    :arg handle: Remote handle to retrieve
    :returns: ``XRD`` instance
    """
    try:
        host = handle.split("@")[1]
    except AttributeError:
        logger.warning("retrieve_diaspora_webfinger: invalid handle given: %s", handle)
        return None
    hostmeta = retrieve_diaspora_host_meta(host)
    if not hostmeta:
        return None
    url = hostmeta.find_link(rels="lrdd").template.replace("{uri}", quote(handle))
    document, code, exception = fetch_document(url)
    if exception:
        return None
    try:
        xrd = XRD.parse_xrd(document)
    except xml.parsers.expat.ExpatError:
        return None
    return xrd


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


def get_public_endpoint(domain):
    return "https://%s/receive/public" % domain
