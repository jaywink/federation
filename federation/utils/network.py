import calendar
import datetime
import logging
import re
import socket
from typing import Optional, Dict
from urllib.parse import quote, urlparse
from uuid import uuid4

import requests
from requests_cache import CachedSession, DO_NOT_CACHE
from requests.exceptions import RequestException, HTTPError, SSLError
from requests.exceptions import ConnectionError
from requests.structures import CaseInsensitiveDict

from federation import __version__
from federation.utils.django import federate, get_requests_cache_backend

if federate():
    import json
    from pprint import pprint

logger = logging.getLogger("federation")

USER_AGENT = "python/federation/%s" % __version__

session = CachedSession('fed_cache', backend=get_requests_cache_backend('fed_cache'))
EXPIRATION = datetime.timedelta(hours=6)

def fetch_content_type(url: str) -> Optional[str]:
    """
    Fetch the HEAD of the remote url to determine the content type.
    """
    try:
        response = session.head(url, headers={'user-agent': USER_AGENT}, timeout=10)
    except RequestException as ex:
        logger.warning("fetch_content_type - %s when fetching url %s", ex, url)
    else:
        return response.headers.get('Content-Type')


def fetch_document(url=None, host=None, path="/", timeout=10, raise_ssl_errors=True, extra_headers=None, cache=True, **kwargs):
    """Helper method to fetch remote document.

    Must be given either the ``url`` or ``host``.
    If ``url`` is given, only that will be tried without falling back to http from https.
    If ``host`` given, `path` will be added to it. Will fall back to http on non-success status code.

    :arg url: Full url to fetch, including protocol
    :arg host: Domain part only without path or protocol
    :arg path: Path without domain (defaults to "/")
    :arg timeout: Seconds to wait for response (defaults to 10)
    :arg raise_ssl_errors: Pass False if you want to try HTTP even for sites with SSL errors (default True)
    :arg extra_headers: Optional extra headers dictionary to add to requests
    :arg kwargs holds extra args passed to requests.get
    :returns: Tuple of document (str or None), status code (int or None) and error (an exception class instance or None)
    :raises ValueError: If neither url nor host are given as parameters
    """
    if not url and not host:
        raise ValueError("Need url or host.")

    logger.debug("fetch_document: url=%s, host=%s, path=%s, timeout=%s, raise_ssl_errors=%s",
                 url, host, path, timeout, raise_ssl_errors)
    headers = {'user-agent': USER_AGENT}
    if extra_headers:
        headers.update(extra_headers)
    if url:
        # Use url since it was given
        logger.debug("fetch_document: trying %s", url)
        try:
            response = session.get(url, timeout=timeout, headers=headers, 
                    expire_after=EXPIRATION if cache else DO_NOT_CACHE, **kwargs)
            logger.debug("fetch_document: found document, code %s", response.status_code)
            response.raise_for_status()
            if not response.encoding: response.encoding = 'utf-8'
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
        response = session.get(url, timeout=timeout, headers=headers)
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
            response = session.get(url, timeout=timeout, headers=headers)
            logger.debug("fetch_document: found document, code %s", response.status_code)
            response.raise_for_status()
            return response.text, response.status_code, None
        except RequestException as ex:
            logger.debug("fetch_document: exception %s", ex)
            return None, None, ex
    except RequestException as ex:
        logger.debug("fetch_document: exception %s", ex)
        return None, None, ex


def fetch_host_ip(host: str) -> str:
    """
    Fetch ip by host
    """
    try:
        ip = socket.gethostbyname(host)
    except socket.gaierror:
        return ''

    return ip


def fetch_file(url: str, timeout: int = 30, extra_headers: Dict = None) -> str:
    """
    Download a file with a temporary name and return the name.
    """
    headers = {'user-agent': USER_AGENT}
    if extra_headers:
        headers.update(extra_headers)
    response = session.get(url, timeout=timeout, headers=headers, stream=True)
    response.raise_for_status()
    name = f"/tmp/{str(uuid4())}"
    with open(name, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    return name


def parse_http_date(date):
    """
    Parse a date format as specified by HTTP RFC7231 section 7.1.1.1.

    The three formats allowed by the RFC are accepted, even if only the first
    one is still in widespread use.

    Return an integer expressed in seconds since the epoch, in UTC.

    Implementation copied from Django.
    https://github.com/django/django/blob/master/django/utils/http.py#L157
    License: BSD 3-clause
    """
    MONTHS = 'jan feb mar apr may jun jul aug sep oct nov dec'.split()
    __D = r'(?P<day>\d{2})'
    __D2 = r'(?P<day>[ \d]\d)'
    __M = r'(?P<mon>\w{3})'
    __Y = r'(?P<year>\d{4})'
    __Y2 = r'(?P<year>\d{2})'
    __T = r'(?P<hour>\d{2}):(?P<min>\d{2}):(?P<sec>\d{2})'
    RFC1123_DATE = re.compile(r'^\w{3}, %s %s %s %s GMT$' % (__D, __M, __Y, __T))
    RFC850_DATE = re.compile(r'^\w{6,9}, %s-%s-%s %s GMT$' % (__D, __M, __Y2, __T))
    ASCTIME_DATE = re.compile(r'^\w{3} %s %s %s %s$' % (__M, __D2, __T, __Y))
    # email.utils.parsedate() does the job for RFC1123 dates; unfortunately
    # RFC7231 makes it mandatory to support RFC850 dates too. So we roll
    # our own RFC-compliant parsing.
    for regex in RFC1123_DATE, RFC850_DATE, ASCTIME_DATE:
        m = regex.match(date)
        if m is not None:
            break
    else:
        raise ValueError("%r is not in a valid HTTP date format" % date)
    try:
        year = int(m.group('year'))
        if year < 100:
            if year < 70:
                year += 2000
            else:
                year += 1900
        month = MONTHS.index(m.group('mon').lower()) + 1
        day = int(m.group('day'))
        hour = int(m.group('hour'))
        min = int(m.group('min'))
        sec = int(m.group('sec'))
        result = datetime.datetime(year, month, day, hour, min, sec)
        return calendar.timegm(result.utctimetuple())
    except Exception as exc:
        raise ValueError("%r is not a valid date" % date) from exc


def send_document(url, data, timeout=10, method="post", *args, **kwargs):
    """Helper method to send a document via POST.

    Additional ``*args`` and ``**kwargs`` will be passed on to ``requests.post``.

    :arg url: Full url to send to, including protocol
    :arg data: Dictionary (will be form-encoded), bytes, or file-like object to send in the body
    :arg timeout: Seconds to wait for response (defaults to 10)
    :arg method: Method to use, defaults to post
    :returns: Tuple of status code (int or None) and error (exception class instance or None)
    """
    if federate():
        try:
            pprint(json.loads(data))
        except:
            pass
        return
    logger.debug("send_document: url=%s, data=%s, timeout=%s, method=%s", url, data, timeout, method)
    if not method:
        method = "post"
    headers = CaseInsensitiveDict({
        'User-Agent': USER_AGENT,
    })
    if "headers" in kwargs:
        # Update from kwargs
        headers.update(kwargs.get("headers"))
    kwargs.update({
        "data": data, "timeout": timeout, "headers": headers
    })
    request_func = getattr(requests, method)
    try:
        response = request_func(url, *args, **kwargs)
        logger.debug("send_document: response status code %s", response.status_code)
        return response.status_code, None
    # TODO support rate limit 429 code
    except RequestException as ex:
        logger.debug("send_document: exception %s", ex)
        return None, ex


def try_retrieve_webfinger_document(resource: str) -> Optional[str]:
    """
    Try to retrieve an RFC7033 webfinger document. Does not raise if it fails.
    """
    if resource.startswith("http://") or resource.startswith("https://"):
        parsed_url = urlparse(resource)
        host = parsed_url.hostname
        request = "/.well-known/webfinger?resource=%s" % quote(resource)
    else:
        try:
            host = resource.split("@")[1]
            request = "/.well-known/webfinger?resource=acct:%s" % quote(resource)
        except (AttributeError, IndexError):
            logger.warning("retrieve_webfinger_document: invalid handle given: %s", resource)
            return None
    document, code, exception = fetch_document(
        host=host, path=request,
    )
    if exception:
        logger.debug("retrieve_webfinger_document: failed to fetch webfinger document: %s, %s", code, exception)
    return document
