import calendar
import datetime
import logging
import re
import socket
from typing import Optional, Tuple
from urllib.parse import quote

import requests
from ipdata import ipdata
from requests.exceptions import RequestException, HTTPError, SSLError
from requests.exceptions import ConnectionError
from requests.structures import CaseInsensitiveDict

from federation import __version__

logger = logging.getLogger("federation")

USER_AGENT = "python/federation/%s" % __version__


def fetch_content_type(url: str) -> Optional[str]:
    """
    Fetch the HEAD of the remote url to determine the content type.
    """
    try:
        response = requests.head(url, headers={'user-agent': USER_AGENT}, timeout=10)
    except RequestException as ex:
        logger.warning("fetch_content_type - %s when fetching url %s", ex, url)
    else:
        return response.headers.get('Content-Type')


def fetch_country_by_ip(ip):
    """
    Fetches country code by IP

    Returns empty string if the request fails in non-200 code.

    Uses the ipdata.co service which has the following rules:

    * Max 1500 requests per day

    See: https://ipdata.co/docs.html#python-library
    """
    iplookup = ipdata.IPData()
    data = iplookup.lookup(ip)
    if data.get('status') != 200:
        return ''

    return data.get('response', {}).get('country_code', '')


def fetch_document(url=None, host=None, path="/", timeout=10, raise_ssl_errors=True, extra_headers=None):
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
            response = requests.get(url, timeout=timeout, headers=headers)
            logger.debug("fetch_document: found document, code %s", response.status_code)
            response.raise_for_status()
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


def fetch_host_ip(host: str) -> str:
    """
    Fetch ip by host
    """
    try:
        ip = socket.gethostbyname(host)
    except socket.gaierror:
        return ''

    return ip


def fetch_host_ip_and_country(host: str) -> Tuple:
    """
    Fetch ip and country by host
    """
    ip = fetch_host_ip(host)
    if not host:
        return '', ''

    country = fetch_country_by_ip(ip)

    return ip, country


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


def try_retrieve_webfinger_document(handle: str) -> Optional[str]:
    """
    Try to retrieve an RFC7033 webfinger document. Does not raise if it fails.
    """
    try:
        host = handle.split("@")[1]
    except AttributeError:
        logger.warning("retrieve_webfinger_document: invalid handle given: %s", handle)
        return None
    document, code, exception = fetch_document(
        host=host, path="/.well-known/webfinger?resource=acct:%s" % quote(handle),
    )
    if exception:
        logger.debug("retrieve_webfinger_document: failed to fetch webfinger document: %s, %s", code, exception)
    return document
