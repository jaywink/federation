# -*- coding: utf-8 -*-
from unittest.mock import Mock

import pytest

from federation.entities.base import BaseEntity, Relationship, Profile, RawContentMixin, GUIDMixin, HandleMixin, \
    PublicMixin, Image, Retraction
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

    def test_entity_calls_main_validate_methods(self):
        post = PostFactory()
        post._validate_required = Mock()
        post._validate_attributes = Mock()
        post._validate_empty_attributes = Mock()
        post._validate_children = Mock()
        post.validate()
        assert post._validate_required.call_count == 1
        assert post._validate_attributes.call_count == 1
        assert post._validate_empty_attributes.call_count == 1
        assert post._validate_children.call_count == 1

    def test_validate_children(self):
        post = PostFactory()
        image = Image()
        profile = Profile()
        post._children = [image]
        post._validate_children()
        post._children = [profile]
        with pytest.raises(ValueError):
            post._validate_children()


class TestGUIDMixinValidate(object):
    def test_validate_guid_raises_on_low_length(self):
        guid = GUIDMixin(guid="x"*15)
        with pytest.raises(ValueError):
            guid.validate()


class TestHandleMixinValidate(object):
    def test_validate_handle_raises_on_invalid_format(self):
        handle = HandleMixin(handle="foobar")
        with pytest.raises(ValueError):
            handle.validate()


class TestPublicMixinValidate(object):
    def test_validate_public_raises_on_low_length(self):
        public = PublicMixin(public="foobar")
        with pytest.raises(ValueError):
            public.validate()


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


class TestImageEntity(object):
    def test_instance_creation(self):
        entity = Image(
            guid="x"*16, handle="foo@example.com", public=False, remote_path="foobar", remote_name="barfoo"
        )
        entity.validate()

    def test_required_fields(self):
        entity = Image(
            guid="x" * 16, handle="foo@example.com", public=False, remote_name="barfoo"
        )
        with pytest.raises(ValueError):
            entity.validate()
        entity = Image(
            guid="x" * 16, handle="foo@example.com", public=False, remote_path="foobar"
        )
        with pytest.raises(ValueError):
            entity.validate()


class TestRetractionEntity(object):
    def test_instance_creation(self):
        entity = Retraction(
            handle="foo@example.com", target_guid="x"*16, entity_type="Post"
        )
        entity.validate()

    def test_required_validates(self):
        entity = Retraction(
            handle="fooexample.com", target_guid="x" * 16, entity_type="Post"
        )
        with pytest.raises(ValueError):
            entity.validate()
        entity = Retraction(
            handle="foo@example.com", target_guid="x" * 15, entity_type="Post"
        )
        with pytest.raises(ValueError):
            entity.validate()
        entity = Retraction(
            handle="foo@example.com", target_guid="x" * 16, entity_type="Foo"
        )
        with pytest.raises(ValueError):
            entity.validate()
