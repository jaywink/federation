import re
from typing import Set, List
from urllib.parse import urlparse

import bleach
from bleach import callbacks
from bs4 import BeautifulSoup
from bs4.element import NavigableString
from commonmark import commonmark

ILLEGAL_TAG_CHARS = "!#$%^&*+.,@£/()=?`'\\{[]}~;:\"’”—\xa0"
TAG_PATTERN = re.compile(r'(^|\s)(#[\w]+)', re.UNICODE)
MENTION_PATTERN = re.compile(r'(^|\s)(@{?[\S ]?[^{}@]+[@;]?\s*[\w\-./@]+[\w/]+}?)', re.UNICODE)


def decode_if_bytes(text):
    try:
        return text.decode("utf-8")
    except AttributeError:
        return text


def encode_if_text(text):
    try:
        return bytes(text, encoding="utf-8")
    except TypeError:
        return text


def find_tags(text: str) -> Set[str]:
    """Find tags in text.

    Ignore tags inside code blocks.

    Returns a set of tags.

    """
    tags = find_elements(BeautifulSoup(commonmark(text, ignore_html_blocks=True), 'html.parser'),
                         TAG_PATTERN)
    return set([tag.text.lstrip('#').lower() for tag in tags])


def find_elements(soup: BeautifulSoup, pattern: re.Pattern) -> List[NavigableString]:
    """
    Split a BeautifulSoup tree strings according to a pattern, replacing each element
    with a NavigableString. The returned list can be used to linkify the found
    elements.

    :param soup: BeautifulSoup instance of the content being searched
    :param pattern: Compiled regular expression defined using a single group
    :return: A NavigableString list attached to the original soup
    """
    for candidate in soup.find_all(string=True):
        if candidate.parent.name == 'code': continue
        ns = [NavigableString(r) for r in re.split(pattern, candidate.text)]
        candidate.replace_with(*ns)
    return list(soup.find_all(string=re.compile(r'\A'+pattern.pattern+r'\Z')))


def get_path_from_url(url: str) -> str:
    """
    Return only the path part of an URL.
    """
    parsed = urlparse(url)
    return parsed.path


def process_text_links(text):
    """Process links in text, adding some attributes and linkifying textual links."""
    link_callbacks = [callbacks.nofollow, callbacks.target_blank]

    def link_attributes(attrs, new=False):
        """Run standard callbacks except for internal links."""
        href_key = (None, "href")
        if attrs.get(href_key, "").startswith("/"):
            return attrs

        # Run the standard callbacks
        for callback in link_callbacks:
            attrs = callback(attrs, new)
        return attrs

    return bleach.linkify(
        text,
        callbacks=[link_attributes],
        parse_email=False,
        skip_tags=["code"],
    )


def test_tag(tag: str) -> bool:
    """Test a word whether it could be accepted as a tag."""
    if not tag:
        return False
    for char in ILLEGAL_TAG_CHARS:
        if char in tag:
            return False
    return True


def validate_handle(handle):
    """
    Very basic handle validation as per
    https://diaspora.github.io/diaspora_federation/federation/types.html#diaspora-id
    """
    return re.match(r"[a-z0-9\-_.]+@[^@/]+\.[^@/]+", handle, flags=re.IGNORECASE) is not None


def with_slash(url):
    if url.endswith('/'):
        return url
    return f"{url}/"
