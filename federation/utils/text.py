import re
from typing import Set, Tuple
from urllib.parse import urlparse

import bleach
from bleach import callbacks

ILLEGAL_TAG_CHARS = "!#$%^&*+.,@£/()=?`'\\{[]}~;:\"’”—\xa0"


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


def find_tags(text: str, replacer: callable = None) -> Tuple[Set, str]:
    """Find tags in text.

    Tries to ignore tags inside code blocks.

    Optionally, if passed a "replacer", will also replace the tag word with the result
    of the replacer function called with the tag word.

    Returns a set of tags and the original or replaced text.
    """
    found_tags = set()
    lines = text.splitlines(keepends=True)
    final_lines = []
    code_block = False
    final_text = None
    # Check each line separately
    for line in lines:
        final_words = []
        if line[0:3] == "```":
            code_block = not code_block
        if line.find("#") == -1 or line[0:4] == "    " or code_block:
            # Just add the whole line
            final_lines.append(line)
            continue
        # Check each word separately
        words = line.split(" ")
        for word in words:
            candidate = word.strip().strip("([]),.!?:")
            if candidate.startswith("#"):
                candidate = candidate.strip("#")
                if test_tag(candidate.lower()):
                    found_tags.add(candidate.lower())
                    if replacer:
                        try:
                            tag_word = word.replace("#%s" % candidate, replacer(candidate))
                            final_words.append(tag_word)
                        except Exception:
                            final_words.append(word)
                else:
                    final_words.append(word)
            else:
                final_words.append(word)
        final_lines.append(" ".join(final_words))
    if replacer:
        final_text = "".join(final_lines)
    return found_tags, final_text or text


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
