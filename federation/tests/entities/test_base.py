# -*- coding: utf-8 -*-
from unittest.mock import Mock

import pytest

from federation.entities.base import BaseEntity
from federation.tests.factories.entities import TaggedPostFactory, PostFactory


class TestPostEntityTags(object):
    def test_post_entity_returns_list_of_tags(self):
        post = TaggedPostFactory()
        assert post.tags == {"tagone", "tagtwo", "tagthree"}


class TestBaseEntityCallsValidateMethods(object):
    def test_entity_calls_attribute_validate_method(self):
        post = PostFactory()
        post.validate_location = Mock()
        post.validate()
        assert post.validate_location.call_count == 1


class TestEntityRequiredAttributes(object):
    def test_entity_checks_for_required_attributes(self):
        entity = BaseEntity()
        entity._required = ["foobar"]
        with pytest.raises(ValueError):
            entity.validate()
