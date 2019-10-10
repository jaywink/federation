from datetime import datetime
from lxml import etree
from unittest.mock import patch, Mock

import pytest

from federation.entities.base import (
    Comment, Post, Reaction, Relationship, Profile, Retraction,
    Follow, Share)
from federation.entities.diaspora.entities import (
    DiasporaPost, DiasporaComment, DiasporaLike,
    DiasporaProfile, DiasporaRetraction, DiasporaContact, DiasporaReshare, DiasporaImage)
from federation.entities.diaspora.mappers import (
    message_to_objects, get_outbound_entity, check_sender_and_entity_handle_match)
from federation.tests.fixtures.payloads import (
    DIASPORA_POST_SIMPLE, DIASPORA_POST_COMMENT, DIASPORA_POST_LIKE,
    DIASPORA_PROFILE, DIASPORA_POST_INVALID, DIASPORA_RETRACTION,
    DIASPORA_POST_WITH_PHOTOS, DIASPORA_CONTACT,
    DIASPORA_PROFILE_EMPTY_TAGS, DIASPORA_RESHARE,
    DIASPORA_RESHARE_WITH_EXTRA_PROPERTIES, DIASPORA_POST_SIMPLE_WITH_MENTION,
    DIASPORA_PROFILE_FIRST_NAME_ONLY, DIASPORA_POST_COMMENT_NESTED)
from federation.types import UserType, ReceiverVariant


class TestDiasporaEntityMappersReceive:
    def test_message_to_objects_mentions_are_extracted(self):
        entities = message_to_objects(
            DIASPORA_POST_SIMPLE_WITH_MENTION, "alice@alice.diaspora.example.org"
        )
        assert len(entities) == 1
        post = entities[0]
        assert post._mentions == {'jaywink@jasonrobinson.me'}

    def test_message_to_objects_simple_post(self):
        entities = message_to_objects(DIASPORA_POST_SIMPLE, "alice@alice.diaspora.example.org")
        assert len(entities) == 1
        post = entities[0]
        assert isinstance(post, DiasporaPost)
        assert isinstance(post, Post)
        assert post.raw_content == "((status message))"
        assert post.guid == "((guidguidguidguidguidguidguid))"
        assert post.handle == "alice@alice.diaspora.example.org"
        assert post.public == False
        assert post.created_at == datetime(2011, 7, 20, 1, 36, 7)
        assert post.provider_display_name == "Socialhome"

    def test_message_to_objects_post_with_photos(self):
        entities = message_to_objects(DIASPORA_POST_WITH_PHOTOS, "alice@alice.diaspora.example.org")
        assert len(entities) == 1
        post = entities[0]
        assert isinstance(post, DiasporaPost)
        photo = post._children[0]
        assert isinstance(photo, DiasporaImage)
        assert photo.url == "https://alice.diaspora.example.org/uploads/images/1234.jpg"
        assert photo.name == ""
        assert photo.raw_content == ""
        assert photo.height == 120
        assert photo.width == 120
        assert photo.guid == "((guidguidguidguidguidguidguif))"
        assert photo.handle == "alice@alice.diaspora.example.org"
        assert photo.created_at == datetime(2011, 7, 20, 1, 36, 7)

    @patch("federation.entities.diaspora.mappers.DiasporaComment._validate_signatures")
    def test_message_to_objects_comment(self, mock_validate):
        entities = message_to_objects(DIASPORA_POST_COMMENT, "alice@alice.diaspora.example.org",
                                      sender_key_fetcher=Mock())
        assert len(entities) == 1
        comment = entities[0]
        assert isinstance(comment, DiasporaComment)
        assert isinstance(comment, Comment)
        assert comment.target_guid == "((parent_guidparent_guidparent_guidparent_guid))"
        assert comment.root_target_guid == ""
        assert comment.guid == "((guidguidguidguidguidguid))"
        assert comment.handle == "alice@alice.diaspora.example.org"
        assert comment.participation == "comment"
        assert comment.raw_content == "((text))"
        assert comment.signature == "((signature))"
        assert comment._xml_tags == [
            "guid", "parent_guid", "text", "author",
        ]
        mock_validate.assert_called_once_with()

    @patch("federation.entities.diaspora.mappers.DiasporaComment._validate_signatures")
    def test_message_to_objects_nested_comment(self, mock_validate):
        entities = message_to_objects(DIASPORA_POST_COMMENT_NESTED, "alice@alice.diaspora.example.org",
                                      sender_key_fetcher=Mock())
        assert len(entities) == 1
        comment = entities[0]
        assert isinstance(comment, DiasporaComment)
        assert isinstance(comment, Comment)
        assert comment.target_guid == "((parent_guidparent_guidparent_guidparent_guid))"
        assert comment.root_target_guid == "((threadparentguid))"
        assert comment.guid == "((guidguidguidguidguidguid))"
        assert comment.handle == "alice@alice.diaspora.example.org"
        assert comment.participation == "comment"
        assert comment.raw_content == "((text))"
        assert comment.signature == "((signature))"
        assert comment._xml_tags == [
            "guid", "parent_guid", "thread_parent_guid", "text", "author",
        ]
        mock_validate.assert_called_once_with()

    @patch("federation.entities.diaspora.mappers.DiasporaLike._validate_signatures")
    def test_message_to_objects_like(self, mock_validate):
        entities = message_to_objects(
            DIASPORA_POST_LIKE, "alice@alice.diaspora.example.org", sender_key_fetcher=Mock()
        )
        assert len(entities) == 1
        like = entities[0]
        assert isinstance(like, DiasporaLike)
        assert isinstance(like, Reaction)
        assert like.target_guid == "((parent_guidparent_guidparent_guidparent_guid))"
        assert like.guid == "((guidguidguidguidguidguid))"
        assert like.handle == "alice@alice.diaspora.example.org"
        assert like.participation == "reaction"
        assert like.reaction == "like"
        assert like.signature == "((signature))"
        assert like._xml_tags == [
            "parent_type", "guid", "parent_guid", "positive", "author",
        ]
        mock_validate.assert_called_once_with()

    @patch("federation.entities.diaspora.mappers.retrieve_and_parse_profile", return_value=Mock(
        id="bob@example.com",
    ))
    def test_message_to_objects_profile(self, mock_parse):
        entities = message_to_objects(DIASPORA_PROFILE, "bob@example.com")
        assert len(entities) == 1
        profile = entities[0]
        assert profile.handle == "bob@example.com"
        assert profile.name == "Bob Bobertson"
        assert profile.image_urls == {
            "large": "https://example.com/uploads/images/thumb_large_c833747578b5.jpg",
            "medium": "https://example.com/uploads/images/thumb_medium_c8b1aab04f3.jpg",
            "small": "https://example.com/uploads/images/thumb_small_c8b147578b5.jpg",
        }
        assert profile.gender == ""
        assert profile.raw_content == "A cool bio"
        assert profile.location == "Helsinki"
        assert profile.public == True
        assert profile.nsfw == False
        assert profile.tag_list == ["socialfederation", "federation"]

    @patch("federation.entities.diaspora.mappers.retrieve_and_parse_profile", return_value=Mock(
        id="bob@example.com",
    ))
    def test_message_to_objects_profile__first_name_only(self, mock_parse):
        entities = message_to_objects(DIASPORA_PROFILE_FIRST_NAME_ONLY, "bob@example.com")
        assert len(entities) == 1
        profile = entities[0]
        assert profile.name == "Bob"

    @patch("federation.entities.diaspora.mappers.retrieve_and_parse_profile", return_value=Mock(
        id="bob@example.com",
    ))
    def test_message_to_objects_profile_survives_empty_tag_string(self, mock_parse):
        entities = message_to_objects(DIASPORA_PROFILE_EMPTY_TAGS, "bob@example.com")
        assert len(entities) == 1

    def test_message_to_objects_receivers_are_saved__followers_receiver(self):
        # noinspection PyTypeChecker
        entities = message_to_objects(
            DIASPORA_POST_SIMPLE,
            "alice@alice.diaspora.example.org",
        )
        entity = entities[0]
        assert entity._receivers == [UserType(
            id="alice@alice.diaspora.example.org", receiver_variant=ReceiverVariant.FOLLOWERS,
        )]

    def test_message_to_objects_receivers_are_saved__single_receiver(self):
        # noinspection PyTypeChecker
        entities = message_to_objects(
            DIASPORA_POST_SIMPLE,
            "alice@alice.diaspora.example.org",
            user=Mock(id="bob@example.com")
        )
        entity = entities[0]
        assert entity._receivers == [UserType(id="bob@example.com", receiver_variant=ReceiverVariant.ACTOR)]

    def test_message_to_objects_retraction(self):
        entities = message_to_objects(DIASPORA_RETRACTION, "bob@example.com")
        assert len(entities) == 1
        entity = entities[0]
        assert isinstance(entity, DiasporaRetraction)
        assert entity.handle == "bob@example.com"
        assert entity.target_guid == "x" * 16
        assert entity.entity_type == "Post"

    def test_message_to_objects_contact(self):
        entities = message_to_objects(DIASPORA_CONTACT, "alice@example.com")
        assert len(entities) == 1
        entity = entities[0]
        assert isinstance(entity, DiasporaContact)
        assert entity.handle == "alice@example.com"
        assert entity.target_handle == "bob@example.org"
        assert entity.following is True

    def test_message_to_objects_reshare(self):
        entities = message_to_objects(DIASPORA_RESHARE, "alice@example.org")
        assert len(entities) == 1
        entity = entities[0]
        assert isinstance(entity, DiasporaReshare)
        assert entity.handle == "alice@example.org"
        assert entity.guid == "a0b53e5029f6013487753131731751e9"
        assert entity.provider_display_name == ""
        assert entity.target_handle == "bob@example.com"
        assert entity.target_guid == "a0b53bc029f6013487753131731751e9"
        assert entity.public is True
        assert entity.entity_type == "Post"
        assert entity.raw_content == ""

    def test_message_to_objects_reshare_extra_properties(self):
        entities = message_to_objects(DIASPORA_RESHARE_WITH_EXTRA_PROPERTIES, "alice@example.org")
        assert len(entities) == 1
        entity = entities[0]
        assert isinstance(entity, DiasporaReshare)
        assert entity.raw_content == "Important note here"
        assert entity.entity_type == "Comment"

    @patch("federation.entities.diaspora.mappers.logger.error")
    def test_invalid_entity_logs_an_error(self, mock_logger):
        entities = message_to_objects(DIASPORA_POST_INVALID, "alice@alice.diaspora.example.org")
        assert len(entities) == 0
        assert mock_logger.called

    def test_adds_source_protocol_to_entity(self):
        entities = message_to_objects(DIASPORA_POST_SIMPLE, "alice@alice.diaspora.example.org")
        assert entities[0]._source_protocol == "diaspora"

    @patch("federation.entities.diaspora.mappers.DiasporaComment._validate_signatures")
    def test_source_object(self, mock_validate):
        entities = message_to_objects(DIASPORA_POST_COMMENT, "alice@alice.diaspora.example.org",
                                      sender_key_fetcher=Mock())
        entity = entities[0]
        assert entity._source_object == etree.tostring(etree.fromstring(DIASPORA_POST_COMMENT))

    @patch("federation.entities.diaspora.mappers.DiasporaComment._validate_signatures")
    def test_element_to_objects_calls_sender_key_fetcher(self, mock_validate):
        mock_fetcher = Mock()
        message_to_objects(DIASPORA_POST_COMMENT, "alice@alice.diaspora.example.org", mock_fetcher)
        mock_fetcher.assert_called_once_with(
            "alice@alice.diaspora.example.org",
        )

    @patch("federation.entities.diaspora.mappers.DiasporaComment._validate_signatures")
    @patch("federation.entities.diaspora.mappers.retrieve_and_parse_profile")
    def test_element_to_objects_calls_retrieve_remote_profile(self, mock_retrieve, mock_validate):
        message_to_objects(DIASPORA_POST_COMMENT, "alice@alice.diaspora.example.org")
        mock_retrieve.assert_called_once_with("alice@alice.diaspora.example.org")

    @patch("federation.entities.diaspora.mappers.check_sender_and_entity_handle_match")
    def test_element_to_objects_verifies_handles_are_the_same(self, mock_check):
        message_to_objects(DIASPORA_POST_SIMPLE, "bob@example.org")
        mock_check.assert_called_once_with("bob@example.org", "alice@alice.diaspora.example.org")

    def test_element_to_objects_returns_no_entity_if_handles_are_different(self):
        entities = message_to_objects(DIASPORA_POST_SIMPLE, "bob@example.org")
        assert not entities


class TestGetOutboundEntity:
    def test_already_fine_entities_are_returned_as_is(self, private_key):
        entity = DiasporaPost()
        entity.validate = Mock()
        assert get_outbound_entity(entity, private_key) == entity
        entity = DiasporaLike()
        entity.validate = Mock()
        assert get_outbound_entity(entity, private_key) == entity
        entity = DiasporaComment()
        entity.validate = Mock()
        assert get_outbound_entity(entity, private_key) == entity
        entity = DiasporaProfile(handle="foobar@example.com", guid="1234")
        entity.validate = Mock()
        assert get_outbound_entity(entity, private_key) == entity
        entity = DiasporaContact()
        entity.validate = Mock()
        assert get_outbound_entity(entity, private_key) == entity
        entity = DiasporaReshare()
        entity.validate = Mock()
        assert get_outbound_entity(entity, private_key) == entity

    @patch.object(DiasporaPost, "validate", new=Mock())
    def test_post_is_converted_to_diasporapost(self, private_key):
        entity = Post()
        assert isinstance(get_outbound_entity(entity, private_key), DiasporaPost)

    @patch.object(DiasporaComment, "validate", new=Mock())
    def test_comment_is_converted_to_diasporacomment(self, private_key):
        entity = Comment()
        assert isinstance(get_outbound_entity(entity, private_key), DiasporaComment)

    @patch.object(DiasporaLike, "validate", new=Mock())
    def test_reaction_of_like_is_converted_to_diasporalike(self, private_key):
        entity = Reaction(reaction="like")
        assert isinstance(get_outbound_entity(entity, private_key), DiasporaLike)

    @patch.object(DiasporaProfile, "validate", new=Mock())
    def test_profile_is_converted_to_diasporaprofile(self, private_key):
        entity = Profile(handle="foobar@example.com", guid="1234")
        assert isinstance(get_outbound_entity(entity, private_key), DiasporaProfile)

    def test_other_reaction_raises(self, private_key):
        entity = Reaction(reaction="foo")
        with pytest.raises(ValueError):
            get_outbound_entity(entity, private_key)

    def test_other_relation_raises(self, private_key):
        entity = Relationship(relationship="foo")
        with pytest.raises(ValueError):
            get_outbound_entity(entity, private_key)

    @patch.object(DiasporaRetraction, "validate", new=Mock())
    def test_retraction_is_converted_to_diasporaretraction(self, private_key):
        entity = Retraction()
        assert isinstance(get_outbound_entity(entity, private_key), DiasporaRetraction)

    @patch.object(DiasporaContact, "validate", new=Mock())
    def test_follow_is_converted_to_diasporacontact(self, private_key):
        entity = Follow()
        assert isinstance(get_outbound_entity(entity, private_key), DiasporaContact)

    @patch.object(DiasporaReshare, "validate", new=Mock())
    def test_share_is_converted_to_diasporareshare(self, private_key):
        entity = Share()
        assert isinstance(get_outbound_entity(entity, private_key), DiasporaReshare)

    def test_signs_relayable_if_no_signature(self, private_key):
        entity = DiasporaComment()
        entity.validate = Mock()
        outbound = get_outbound_entity(entity, private_key)
        assert outbound.signature != ""

    def test_returns_entity_if_outbound_doc_on_entity(self, private_key):
        entity = Comment()
        entity.outbound_doc = "foobar"
        assert get_outbound_entity(entity, private_key) == entity

    def test_entity_is_validated__fail(self, private_key):
        entity = Share(
            actor_id="foobar@localhost.local",
            handle="foobar@localhost.local",
            id="1"*16,
            guid="1"*16,
            created_at=datetime.now(),
            target_id="2" * 16,
        )
        with pytest.raises(ValueError):
            get_outbound_entity(entity, private_key)

    def test_entity_is_validated__success(self, private_key):
        entity = Share(
            actor_id="foobar@localhost.local",
            handle="foobar@localhost.local",
            id="1" * 16,
            guid="1" * 16,
            created_at=datetime.now(),
            target_handle="barfoo@remote.local",
            target_id="2" * 16,
            target_guid="2" * 16,
        )
        get_outbound_entity(entity, private_key)


def test_check_sender_and_entity_handle_match():
    assert not check_sender_and_entity_handle_match("foo", "bar")
    assert check_sender_and_entity_handle_match("foo", "foo")
