import datetime
import re
from unittest.mock import patch, Mock

import arrow
from lxml import etree

from federation.entities.base import Post, Profile
from federation.entities.diaspora.entities import DiasporaPost
from federation.entities.diaspora.utils import (
    get_full_xml_representation, format_dt, add_element_to_doc)
from federation.entities.utils import get_base_attributes


class TestGetBaseAttributes:
    def test_get_base_attributes_returns_only_intended_attributes(self):
        entity = Post()
        attrs = get_base_attributes(entity).keys()
        assert set(attrs) == {
            "created_at", "location", "provider_display_name", "public", "raw_content",
            "signature", "base_url", "actor_id", "id", "handle", "guid", "activity", "activity_id",
            "url",
        }
        entity = Profile()
        attrs = get_base_attributes(entity).keys()
        assert set(attrs) == {
            "created_at", "name", "email", "gender", "raw_content", "location", "public",
            "nsfw", "public_key", "image_urls", "tag_list", "signature", "url", "atom_url",
            "base_url", "id", "actor_id", "handle", "handle", "guid", "activity", "activity_id", "username",
            "inboxes", "mxid",
        }


class TestGetFullXMLRepresentation:
    @patch.object(DiasporaPost, "validate", new=Mock())
    def test_returns_xml_document(self):
        entity = Post()
        document = get_full_xml_representation(entity, "")
        document = re.sub(r"<created_at>.*</created_at>", "", document)  # Dates are annoying to compare
        assert document == "<XML><post><status_message><text></text><guid></guid>" \
                           "<author></author><public>false</public>" \
                           "<provider_display_name></provider_display_name></status_message></post></XML>"


class TestFormatDt:
    def test_formatted_string_returned_from_tz_aware_datetime(self):
        dt = arrow.get(datetime.datetime(2017, 1, 28, 3, 2, 3), "Europe/Helsinki").datetime
        assert format_dt(dt) == "2017-01-28T01:02:03Z"


def test_add_element_to_doc():
    # Replacing value
    doc = etree.fromstring("<comment><text>foobar</text><parent_author_signature>barfoo</parent_author_signature>"
                           "</comment>")
    add_element_to_doc(doc, "parent_author_signature", "newsig")
    assert etree.tostring(doc) == b"<comment><text>foobar</text><parent_author_signature>newsig" \
                                  b"</parent_author_signature></comment>"
    # Adding value to an empty tag
    doc = etree.fromstring("<comment><text>foobar</text><parent_author_signature /></comment>")
    add_element_to_doc(doc, "parent_author_signature", "newsig")
    assert etree.tostring(doc) == b"<comment><text>foobar</text><parent_author_signature>newsig" \
                                  b"</parent_author_signature></comment>"
    # Adding missing tag
    doc = etree.fromstring("<comment><text>foobar</text></comment>")
    add_element_to_doc(doc, "parent_author_signature", "newsig")
    assert etree.tostring(doc) == b"<comment><text>foobar</text><parent_author_signature>newsig" \
                                  b"</parent_author_signature></comment>"
