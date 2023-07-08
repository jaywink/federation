from unittest.mock import Mock

import pytest

from federation.entities.base import Relationship, Profile, Image
from federation.entities.mixins import PublicMixin, RawContentMixin, BaseEntity
from federation.tests.factories.entities import TaggedPostFactory, PostFactory, ShareFactory, RetractionFactory, \
    ImageFactory, FollowFactory


class TestPostEntityTags:
    def test_post_entity_returns_list_of_tags(self):
        post = TaggedPostFactory()
        assert post.tags == ["snakecase", "tagone", "tagthree", "tagtwo", "upper"]

    def test_post_entity_without_raw_content_tags_returns_empty_set(self):
        post = PostFactory(raw_content=None)
        assert post.tags == []


class TestBaseEntityCallsValidateMethods:
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


class TestPublicMixinValidate:
    def test_validate_public_raises_on_low_length(self):
        public = PublicMixin(public="foobar")
        with pytest.raises(ValueError):
            public.validate()


class TestEntityRequiredAttributes:
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


class TestRelationshipEntity:
    def test_instance_creation(self):
        entity = Relationship(handle="bob@example.com", target_handle="alice@example.com", relationship="following")
        assert entity

    def test_instance_creation_validates_relationship_value(self):
        with pytest.raises(ValueError):
            entity = Relationship(handle="bob@example.com", target_handle="alice@example.com", relationship="hating")
            entity.validate()


class TestProfileEntity:
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


class TestImageEntity:
    def test_instance_creation(self):
        entity = ImageFactory()
        entity.validate()


class TestRetractionEntity:
    def test_instance_creation(self):
        entity = RetractionFactory()
        entity.validate()


class TestFollowEntity:
    def test_instance_creation(self):
        entity = FollowFactory()
        entity.validate()


class TestShareEntity:
    def test_instance_creation(self):
        entity = ShareFactory()
        entity.validate()


class TestRawContentMixin:
    @pytest.mark.skip
    def test_rendered_content(self, post):
        assert post.rendered_content == """<p>One more test before sleep 😅 This time with an image.</p>
<p><img src="https://jasonrobinson.me/media/uploads/2020/12/27/1b2326c6-554c-4448-9da3-bdacddf2bb77.jpeg" alt=""></p>"""
