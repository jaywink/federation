# -*- coding: utf-8 -*-
import re

from federation.entities.base import Post
from federation.entities.diaspora.utils import get_base_attributes, get_full_xml_representation


class TestGetBaseAttributes(object):
    def test_get_base_attributes_returns_only_intended_attributes(self):
        entity = Post()
        attrs = get_base_attributes(entity).keys()
        assert set(attrs) == {
            'created_at', 'guid', 'handle', 'location', 'photos', 'provider_display_name', 'public', 'raw_content'
        }


class TestGetFullXMLRepresentation(object):
    def test_returns_xml_document(self):
        entity = Post()
        document = get_full_xml_representation(entity)
        document = re.sub(r"<created_at>.*</created_at>", "", document)  # Dates are annoying to compare
        assert document == "<XML><post><status_message><raw_message></raw_message><guid></guid>" \
                           "<diaspora_handle></diaspora_handle><public>false</public>" \
                           "<provider_display_name></provider_display_name></status_message></post></XML>"
