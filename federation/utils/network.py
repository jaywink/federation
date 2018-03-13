# -*- coding: utf-8 -*-
import logging

import requests
from requests.exceptions import RequestException, HTTPError, SSLError
from requests.exceptions import ConnectionError
from requests.structures import CaseInsensitiveDict

from federation import __version__

logger = logging.getLogger("federation")

USER_AGENT = "python/federation/%s" % __version__


def fetch_document(url=None, host=None, path="/", timeout=10, raise_ssl_errors=True):
    """Helper method to fetch remote document.

    Must be given either the ``url`` or ``host``.
    If ``url`` is given, only that will be tried without falling back to http from https.
    If ``host`` given, `path` will be added to it. Will fall back to http on non-success status code.

    :arg url: Full url to fetch, including protocol
    :arg host: Domain part only without path or protocol
    :arg path: Path without domain (defaults to "/")
    :arg timeout: Seconds to wait for response (defaults to 10)
    :arg raise_ssl_errors: Pass False if you want to try HTTP even for sites with SSL errors (default True)
    :returns: Tuple of document (str or None), status code (int or None) and error (an exception class instance or None)
    :raises ValueError: If neither url nor host are given as parameters
    """
    if not url and not host:
        raise ValueError("Need url or host.")

    logger.debug("fetch_document: url=%s, host=%s, path=%s, timeout=%s, raise_ssl_errors=%s",
                 url, host, path, timeout, raise_ssl_errors)
    headers = {'user-agent': USER_AGENT}
    if url:
        # Use url since it was given
        logger.debug("fetch_document: trying %s", url)
        try:
            response = requests.get(url, timeout=timeout, headers=headers)
            logger.debug("fetch_document: found document, code %s", response.status_code)
            return response.text, response.status_code, None
        except RequestException as ex:
            logger.debug("fetch_document: exception %s", ex)
            return None, None, ex
    # Build url with some little sanitizing
    host_string = host.replace("http://", "").replace("https://", "").strip("/")
    path_string = path if path.startswith("/") else "/%s" % path
    url = "https://%s%s" % (host_string, path_string)
    logger.debug("fetch_document: trying %s", url)
    try:
        response = requests.get(url, timeout=timeout, headers=headers)
        logger.debug("fetch_document: found document, code %s", response.status_code)
        response.raise_for_status()
        return response.text, response.status_code, None
    except (HTTPError, SSLError, ConnectionError) as ex:
        if isinstance(ex, SSLError) and raise_ssl_errors:
            logger.debug("fetch_document: exception %s", ex)
            return None, None, ex
        # Try http then
        url = url.replace("https://", "http://")
        logger.debug("fetch_document: trying %s", url)
        try:
            response = requests.get(url, timeout=timeout, headers=headers)
            logger.debug("fetch_document: found document, code %s", response.status_code)
            response.raise_for_status()
            return response.text, response.status_code, None
        except RequestException as ex:
            logger.debug("fetch_document: exception %s", ex)
            return None, None, ex
    except RequestException as ex:
        logger.debug("fetch_document: exception %s", ex)
        return None, None, ex


def send_document(url, data, timeout=10, *args, **kwargs):
    """Helper method to send a document via POST.

    Additional ``*args`` and ``**kwargs`` will be passed on to ``requests.post``.

    :arg url: Full url to send to, including protocol
    :arg data: Dictionary (will be form-encoded), bytes, or file-like object to send in the body
    :arg timeout: Seconds to wait for response (defaults to 10)
    :returns: Tuple of status code (int or None) and error (exception class instance or None)
    """
    logger.debug("send_document: url=%s, data=%s, timeout=%s", url, data, timeout)
    headers = CaseInsensitiveDict({
        'User-Agent': USER_AGENT,
    })
    if "headers" in kwargs:
        # Update from kwargs
        headers.update(kwargs.get("headers"))
    kwargs.update({
        "data": data, "timeout": timeout, "headers": headers
    })
    try:
        response = requests.post(url, *args, **kwargs)
        logger.debug("send_document: response status code %s", response.status_code)
        return response.status_code, None
    except RequestException as ex:
        logger.debug("send_document: exception %s", ex)
        return None, ex
