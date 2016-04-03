# -*- coding: utf-8 -*-
from unittest.mock import patch

from lxml import etree

from federation.entities.base import Post
from federation.entities.diaspora.entities import DiasporaComment
from federation.entities.diaspora.generators import EntityConverter


class TestEntityConverterCallsToXML(object):

    def test_entity_converter_call_to_xml(self):
        entity = Post()

        with patch.object(EntityConverter, "post_to_xml", return_value="foo") as mock_to_xml:
            entity_converter = EntityConverter(entity=entity)
            result = entity_converter.convert_to_xml()
            assert result == "foo"
            assert mock_to_xml.called

    def test_entity_converter_converts_a_post(self):
        entity = Post(raw_content="raw_content", guid="guid", handle="handle", public=True)
        entity_converter = EntityConverter(entity)
        result = entity_converter.convert_to_xml()
        assert result.tag == "status_message"
        assert len(result.find("created_at").text) > 0
        result.find("created_at").text = ""  # timestamp makes testing painful
        converted = b"<status_message><raw_message>raw_content</raw_message><guid>guid</guid>" \
                    b"<diaspora_handle>handle</diaspora_handle><public>true</public><created_at>" \
                    b"</created_at></status_message>"
        assert etree.tostring(result) == converted

    def test_entity_converter_converts_a_comment(self):
        entity = DiasporaComment(raw_content="raw_content", guid="guid", target_guid="target_guid", handle="handle")
        entity_converter = EntityConverter(entity)
        result = entity_converter.convert_to_xml()
        assert result.tag == "comment"
        converted = b"<comment><guid>guid</guid><parent_guid>target_guid</parent_guid>" \
                    b"<author_signature></author_signature><text>raw_content</text>" \
                    b"<diaspora_handle>handle</diaspora_handle></comment>"
        assert etree.tostring(result) == converted
