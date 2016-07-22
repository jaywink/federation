# -*- coding: utf-8 -*-
import logging

import requests
from requests.exceptions import RequestException, HTTPError, SSLError

from federation import __version__

logger = logging.getLogger("social-federation")

USER_AGENT = "python/social-federation/%s" % __version__


def fetch_document(url=None, host=None, path="/", timeout=10, raise_ssl_errors=True):
    """Helper method to fetch remote document.

    Must be given either the `url` or `host`.
    If `url` is given, only that will be tried without falling back to http from https.
    If `host` given, `path` will be added to it. Will fall back to http on non-success status code.

    Args:
        url (str) - Full url to fetch, including protocol
        host (str) - Domain part only without path or protocol
        path (str) - Path without domain (defaults to "/")
        timeout (int) - Seconds to wait for response (defaults to 10)
        raise_ssl_errors (bool) - Pass False if you want to try HTTP even for sites with SSL errors (default True)

    Returns:
        document (str) - The full document or None
        status_code (int) - Status code returned or None
        error (obj) - Exception raised, if any
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
    except (HTTPError, SSLError) as ex:
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
