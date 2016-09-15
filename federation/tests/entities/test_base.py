# -*- coding: utf-8 -*-
from unittest.mock import Mock

import pytest

from federation.entities.base import BaseEntity, Relationship, Profile, RawContentMixin
from federation.tests.factories.entities import TaggedPostFactory, PostFactory


class TestPostEntityTags(object):
    def test_post_entity_returns_list_of_tags(self):
        post = TaggedPostFactory()
        assert post.tags == {"tagone", "tagtwo", "tagthree"}

    def test_post_entity_without_raw_content_tags_returns_empty_set(self):
        post = PostFactory(raw_content=None)
        assert post.tags == set()


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

    def test_validate_checks_required_values_are_not_empty(self):
        entity = RawContentMixin(raw_content=None)
        with pytest.raises(ValueError):
            entity.validate()
        entity = RawContentMixin(raw_content="")
        with pytest.raises(ValueError):
            entity.validate()


class TestRelationshipEntity(object):
    def test_instance_creation(self):
        entity = Relationship(handle="bob@example.com", target_handle="alice@example.com", relationship="following")
        assert entity

    def test_instance_creation_validates_relationship_value(self):
        with pytest.raises(ValueError):
            entity = Relationship(handle="bob@example.com", target_handle="alice@example.com", relationship="hating")
            entity.validate()

    def test_instance_creation_validates_target_handle_value(self):
        with pytest.raises(ValueError):
            entity = Relationship(handle="bob@example.com", target_handle="fefle.com", relationship="following")
            entity.validate()


class TestProfileEntity(object):
    def test_instance_creation(self):
        entity = Profile(handle="bob@example.com", raw_content="foobar")
        assert entity

    def test_instance_creation_validates_email_value(self):
        with pytest.raises(ValueError):
            entity = Profile(handle="bob@example.com", raw_content="foobar", email="foobar")
            entity.validate()

    def test_guid_is_mandatory(self):
        entity = Profile(handle="bob@example.com", raw_content="foobar")
        with pytest.raises(ValueError):
            entity.validate()
