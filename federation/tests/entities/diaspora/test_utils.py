# -*- coding: utf-8 -*-
from federation.entities.base import Post
from federation.entities.diaspora.utils import get_base_attributes


class TestGetBaseAttributes(object):
    def test_get_base_attributes_returns_only_intended_attributes(self):
        entity = Post()
        attrs = get_base_attributes(entity).keys()
        assert set(attrs) == {
            'created_at', 'guid', 'handle', 'location', 'photos', 'provider_display_name', 'public', 'raw_content'
        }
