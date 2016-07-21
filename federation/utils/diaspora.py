# -*- coding: utf-8 -*-
from urllib.parse import quote

from xrd import XRD

from federation.utils.network import fetch_document


def retrieve_diaspora_hcard(handle):
    """Retrieve a remote Diaspora hCard document.

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
    """Retrieve a remote Diaspora webfinger document.

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
    """Retrieve a remote Diaspora host-meta document.

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
