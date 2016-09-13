# -*- coding: utf-8 -*-
from urllib.parse import quote, urlparse

from lxml import html
from xrd import XRD

from federation.entities.base import Profile
from federation.utils.network import fetch_document


def retrieve_diaspora_hcard(handle):
    """
    Retrieve a remote Diaspora hCard document.

    Args:
        handle (str) - Remote handle to retrieve

    Returns:
        str (HTML document)
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

    Args:
        handle (str) - Remote handle to retrieve

    Returns:
        XRD
    """
    hostmeta = retrieve_diaspora_host_meta(handle.split("@")[1])
    if not hostmeta:
        return None
    url = hostmeta.find_link(rels="lrdd").template.replace("{uri}", quote(handle))
    document, code, exception = fetch_document(url)
    if exception:
        return None
    xrd = XRD.parse_xrd(document)
    return xrd


def retrieve_diaspora_host_meta(host):
    """
    Retrieve a remote Diaspora host-meta document.

    Args:
        host (str) - Host to retrieve from

    Returns:
        XRD
    """
    document, code, exception = fetch_document(host=host, path="/.well-known/host-meta")
    if exception:
        return None
    xrd = XRD.parse_xrd(document)
    return xrd


def _get_element_text_or_none(document, selector):
    """
    Using a CSS selector, get the element and return the text, or None if no element.

    Args:
        document (HTMLElement) - HTMLElement document
        selector (str) - CSS selector
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


def parse_profile_from_hcard(hcard):
    """
    Parse all the fields we can from a hCard document to get a Profile.

    Args:
         hcard (str) - HTML hcard document
    """
    doc = html.fromstring(hcard)
    domain = urlparse(_get_element_attr_or_none(doc, "a#pod_location", "href")).netloc
    profile = Profile(
        name=_get_element_text_or_none(doc, ".fn"),
        image_urls={
            "small": _get_element_attr_or_none(doc, ".entity_photo_small .photo", "src"),
            "medium": _get_element_attr_or_none(doc, ".entity_photo_medium .photo", "src"),
            "large": _get_element_attr_or_none(doc, ".entity_photo .photo", "src"),
        },
        public=True if _get_element_text_or_none(doc, ".searchable") == "true" else False,
        handle="%s@%s" % (_get_element_text_or_none(doc, ".nickname"), domain),
        guid=_get_element_text_or_none(doc, ".uid"),
        public_key=_get_element_text_or_none(doc, ".key"),
    )
    return profile


def retrieve_and_parse_profile(handle):
    """
    Retrieve the remote user and return a Profile object.

    Args:
        handle (str) - User handle in username@domain.tld format

    Returns:
        Profile
    """
    hcard = retrieve_diaspora_hcard(handle)
    if not hcard:
        return None
    return parse_profile_from_hcard(hcard)
