import re
from typing import Set, List
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from bs4.element import NavigableString
from commonmark import commonmark

ILLEGAL_TAG_CHARS = "!#$%^&*+.,@£/()=?`'\\{[]}~;:\"’”—\xa0"
TAG_PATTERN = re.compile(r'(#[\w\-]+)([)\]_!?*%/.,;\s]+\s*|\Z)', re.UNICODE)
# This will match non matching braces. I don't think it's an issue.
MENTION_PATTERN = re.compile(r'(@\{?(?:[\w\-. \u263a-\U0001f645]*; *)?[\w]+@[\w\-.]+\.[\w]+}?)', re.UNICODE)
URL_PATTERN = re.compile(r'(^|[#*_\s])((?:https?://)?[\w\-.]+\.[\w]{1}[\w_\-.#?&/~@!$()*,;%=+]*)', re.UNICODE)

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
    found = []
    for candidate in soup.find_all(string=True):
        parent = candidate.find_parent()
        if parent.name == 'code': continue
        ns = [NavigableString(r) for r in re.split(pattern, candidate.text)]
        if ns:
            candidate.replace_with(*ns)
            found.extend([child for child in parent.find_all(
                string=re.compile(r'\A'+pattern.pattern+r'\Z')) if child in ns])
    return found


def get_path_from_url(url: str) -> str:
    """
    Return only the path part of an URL.
    """
    parsed = urlparse(url)
    return parsed.path



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
