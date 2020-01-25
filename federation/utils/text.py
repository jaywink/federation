import re
from urllib.parse import urlparse

import bleach
from bleach import callbacks


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
        if attrs.get(href_key).startswith("/"):
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
