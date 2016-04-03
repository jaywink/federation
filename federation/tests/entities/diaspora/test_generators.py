# -*- coding: utf-8 -*-
from datetime import datetime
from lxml import etree
from unittest.mock import patch

from federation.entities.base import Post
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
        entity = Post(raw_content="raw_content", guid="guid", handle="handle", public=True, created_at=datetime.today())
        entity_converter = EntityConverter(entity)
        result = entity_converter.convert_to_xml()
        assert result.tag == "status_message"
        assert len(result.find("created_at").text) > 0
        result.find("created_at").text = ""  # timestamp makes testing painful
        post_converted = b"<status_message><raw_message>raw_content</raw_message><guid>guid</guid>" \
                         b"<diaspora_handle>handle</diaspora_handle><public>true</public><created_at>" \
                         b"</created_at></status_message>"
        assert etree.tostring(result) == post_converted
