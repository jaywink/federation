from unittest.mock import patch

import pytest

from federation.entities.activitypub.entities import (
    ActivitypubFollow, ActivitypubAccept, ActivitypubProfile, ActivitypubPost, ActivitypubComment,
    ActivitypubRetraction, ActivitypubShare)
from federation.entities.activitypub.mappers import message_to_objects, get_outbound_entity
from federation.entities.base import Accept, Follow, Profile, Post, Comment, Image
from federation.tests.fixtures.payloads import (
    ACTIVITYPUB_FOLLOW, ACTIVITYPUB_PROFILE, ACTIVITYPUB_PROFILE_INVALID, ACTIVITYPUB_UNDO_FOLLOW, ACTIVITYPUB_POST,
    ACTIVITYPUB_COMMENT, ACTIVITYPUB_RETRACTION, ACTIVITYPUB_SHARE, ACTIVITYPUB_RETRACTION_SHARE,
    ACTIVITYPUB_POST_IMAGES, ACTIVITYPUB_POST_WITH_SOURCE_MARKDOWN, ACTIVITYPUB_POST_WITH_TAGS,
    ACTIVITYPUB_POST_WITH_SOURCE_BBCODE, ACTIVITYPUB_POST_WITH_MENTIONS)
from federation.types import UserType, ReceiverVariant


class TestActivitypubEntityMappersReceive:
    @patch.object(ActivitypubFollow, "post_receive", autospec=True)
    def test_message_to_objects__calls_post_receive_hook(self, mock_post_receive):
        message_to_objects(ACTIVITYPUB_FOLLOW, "https://example.com/actor")
        assert mock_post_receive.called

    def test_message_to_objects__announce(self):
        entities = message_to_objects(ACTIVITYPUB_SHARE, "https://mastodon.social/users/jaywink")
        assert len(entities) == 1
        entity = entities[0]
        assert isinstance(entity, ActivitypubShare)
        assert entity.actor_id == "https://mastodon.social/users/jaywink"
        assert entity.target_id == "https://mastodon.social/users/Gargron/statuses/102559779793316012"
        assert entity.id == "https://mastodon.social/users/jaywink/statuses/102560701449465612/activity"
        assert entity.public is True
        assert entity.entity_type == "Post"
        assert entity.raw_content == ""

    def test_message_to_objects__follow(self):
        entities = message_to_objects(ACTIVITYPUB_FOLLOW, "https://example.com/actor")
        assert len(entities) == 1
        entity = entities[0]
        assert isinstance(entity, ActivitypubFollow)
        assert entity.actor_id == "https://example.com/actor"
        assert entity.target_id == "https://example.org/actor"
        assert entity.following is True

    def test_message_to_objects__unfollow(self):
        entities = message_to_objects(ACTIVITYPUB_UNDO_FOLLOW, "https://example.com/actor")
        assert len(entities) == 1
        entity = entities[0]
        assert isinstance(entity, ActivitypubFollow)
        assert entity.actor_id == "https://example.com/actor"
        assert entity.target_id == "https://example.org/actor"
        assert entity.following is False

    @pytest.mark.skip
    def test_message_to_objects_mentions_are_extracted(self):
        entities = message_to_objects(
            DIASPORA_POST_SIMPLE_WITH_MENTION, "alice@alice.diaspora.example.org"
        )
        assert len(entities) == 1
        post = entities[0]
        assert post._mentions == {'jaywink@jasonrobinson.me'}

    def test_message_to_objects_simple_post(self):
        entities = message_to_objects(ACTIVITYPUB_POST, "https://diaspodon.fr/users/jaywink")
        assert len(entities) == 1
        post = entities[0]
        assert isinstance(post, ActivitypubPost)
        assert isinstance(post, Post)
        assert post.raw_content == '[@jaywink](https://dev.jasonrobinson.me/u/jaywink/) boom'
        assert post.rendered_content == '<p><span class="h-card"><a href="https://dev.jasonrobinson.me/u/jaywink/" ' \
                                        'class="u-url mention">@<span>jaywink</span></a></span> boom</p>'
        assert post.id == "https://diaspodon.fr/users/jaywink/statuses/102356911717767237"
        assert post.actor_id == "https://diaspodon.fr/users/jaywink"
        assert post.public is True
        assert post._media_type == "text/html"
        assert getattr(post, "target_id", None) is None

    def test_message_to_objects_simple_post__with_mentions(self):
        entities = message_to_objects(ACTIVITYPUB_POST_WITH_TAGS, "https://diaspodon.fr/users/jaywink")
        assert len(entities) == 1
        post = entities[0]
        assert isinstance(post, ActivitypubPost)
        assert isinstance(post, Post)
        assert post.raw_content == 'boom #test'

    def test_message_to_objects_simple_post__with_tags(self):
        entities = message_to_objects(ACTIVITYPUB_POST_WITH_MENTIONS, "https://mastodon.social/users/jaywink")
        assert len(entities) == 1
        post = entities[0]
        assert isinstance(post, ActivitypubPost)
        assert isinstance(post, Post)
        assert len(post._mentions) == 1

    def test_message_to_objects_simple_post__with_source__bbcode(self):
        entities = message_to_objects(ACTIVITYPUB_POST_WITH_SOURCE_BBCODE, "https://diaspodon.fr/users/jaywink")
        assert len(entities) == 1
        post = entities[0]
        assert isinstance(post, ActivitypubPost)
        assert isinstance(post, Post)
        assert post.rendered_content == '<p><span class="h-card"><a href="https://dev.jasonrobinson.me/u/jaywink/" ' \
                                        'class="u-url mention">@<span>jaywink</span></a></span> boom</p>'
        assert post.raw_content == '[@jaywink](https://dev.jasonrobinson.me/u/jaywink/) boom\n\n'

    def test_message_to_objects_simple_post__with_source__markdown(self):
        entities = message_to_objects(ACTIVITYPUB_POST_WITH_SOURCE_MARKDOWN, "https://diaspodon.fr/users/jaywink")
        assert len(entities) == 1
        post = entities[0]
        assert isinstance(post, ActivitypubPost)
        assert isinstance(post, Post)
        assert post.rendered_content == '<p><span class="h-card"><a href="https://dev.jasonrobinson.me/u/jaywink/" ' \
                                        'class="u-url mention">@<span>jaywink</span></a></span> boom</p>'
        assert post.raw_content == "@jaywink boom"
        assert post.id == "https://diaspodon.fr/users/jaywink/statuses/102356911717767237"
        assert post.actor_id == "https://diaspodon.fr/users/jaywink"
        assert post.public is True
        assert post._media_type == "text/markdown"
        assert getattr(post, "target_id", None) is None

    def test_message_to_objects_post_with_photos(self):
        entities = message_to_objects(ACTIVITYPUB_POST_IMAGES, "https://mastodon.social/users/jaywink")
        assert len(entities) == 1
        post = entities[0]
        assert isinstance(post, ActivitypubPost)
        assert len(post._children) == 1
        photo = post._children[0]
        assert isinstance(photo, Image)
        assert photo.url == "https://files.mastodon.social/media_attachments/files/017/642/079/original/" \
                            "f51b0aee0ee1f2e1.jpg"
        assert photo.name == ""
        assert photo.raw_content == ""
        assert photo.height == 0
        assert photo.width == 0
        assert photo.guid == ""
        assert photo.handle == ""

    def test_message_to_objects_comment(self):
        entities = message_to_objects(ACTIVITYPUB_COMMENT, "https://diaspodon.fr/users/jaywink")
        assert len(entities) == 1
        comment = entities[0]
        assert isinstance(comment, ActivitypubComment)
        assert isinstance(comment, Comment)
        assert comment.raw_content == '[@jaywink](https://dev.jasonrobinson.me/u/jaywink/) boom'
        assert comment.id == "https://diaspodon.fr/users/jaywink/statuses/102356911717767237"
        assert comment.actor_id == "https://diaspodon.fr/users/jaywink"
        assert comment.target_id == "https://dev.jasonrobinson.me/content/653bad70-41b3-42c9-89cb-c4ee587e68e4/"

    @pytest.mark.skip
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

    def test_message_to_objects_profile(self):
        entities = message_to_objects(ACTIVITYPUB_PROFILE, "http://example.com/1234")
        assert len(entities) == 1
        profile = entities[0]
        assert profile.id == "https://diaspodon.fr/users/jaywink"
        assert profile.handle == ""
        assert profile.name == "Jason Robinson"
        assert profile.image_urls == {
            "large": "https://diaspodon.fr/system/accounts/avatars/000/033/155/original/pnc__picked_media_be51984c-4"
                     "3e9-4266-9b9a-b74a61ae4167.jpg?1538505110",
            "medium": "https://diaspodon.fr/system/accounts/avatars/000/033/155/original/pnc__picked_media_be51984c-4"
                      "3e9-4266-9b9a-b74a61ae4167.jpg?1538505110",
            "small": "https://diaspodon.fr/system/accounts/avatars/000/033/155/original/pnc__picked_media_be51984c-4"
                     "3e9-4266-9b9a-b74a61ae4167.jpg?1538505110",
        }
        assert profile.gender == ""
        assert profile.raw_content == "<p>Temp account while implementing AP for Socialhome.</p><p><a href=\"" \
                                      "https://jasonrobinson.me\" rel=\"nofollow noopener\" target=\"_blank\">" \
                                      "<span class=\"invisible\">https://</span><span class=\"\">jasonrobinson." \
                                      "me</span><span class=\"invisible\"></span></a> / <a href=\"https://social" \
                                      "home.network\" rel=\"nofollow noopener\" target=\"_blank\"><span class=\"i" \
                                      "nvisible\">https://</span><span class=\"\">socialhome.network</span><span c" \
                                      "lass=\"invisible\"></span></a> / <a href=\"https://feneas.org\" rel=\"nofoll" \
                                      "ow noopener\" target=\"_blank\"><span class=\"invisible\">https://</span><spa" \
                                      "n class=\"\">feneas.org</span><span class=\"invisible\"></span></a></p>"
        assert profile.location == ""
        assert profile.public is True
        assert profile.nsfw is False
        assert profile.tag_list == []

    def test_message_to_objects_receivers_are_saved(self):
        # noinspection PyTypeChecker
        entities = message_to_objects(
            ACTIVITYPUB_POST,
            "https://diaspodon.fr/users/jaywink",
        )
        entity = entities[0]

        assert set(entity._receivers) == {
            UserType(
                id='https://diaspodon.fr/users/jaywink', receiver_variant=ReceiverVariant.FOLLOWERS,
            ),
            UserType(
                id='https://dev.jasonrobinson.me/p/d4574854-a5d7-42be-bfac-f70c16fcaa97/',
                receiver_variant=ReceiverVariant.ACTOR,
            )
        }

    def test_message_to_objects_retraction(self):
        entities = message_to_objects(ACTIVITYPUB_RETRACTION, "https://friendica.feneas.org/profile/jaywink")
        assert len(entities) == 1
        entity = entities[0]
        assert isinstance(entity, ActivitypubRetraction)
        assert entity.actor_id == "https://friendica.feneas.org/profile/jaywink"
        assert entity.target_id == "https://friendica.feneas.org/objects/76158462-165d-3386-aa23-ba2090614385"
        assert entity.entity_type == "Object"

    def test_message_to_objects_retraction__share(self):
        entities = message_to_objects(ACTIVITYPUB_RETRACTION_SHARE, "https://mastodon.social/users/jaywink")
        assert len(entities) == 1
        entity = entities[0]
        assert isinstance(entity, ActivitypubRetraction)
        assert entity.actor_id == "https://mastodon.social/users/jaywink"
        assert entity.target_id == "https://mastodon.social/users/jaywink/statuses/102571932479036987/activity"
        assert entity.entity_type == "Object"

    @pytest.mark.skip
    def test_message_to_objects_reshare_extra_properties(self):
        entities = message_to_objects(DIASPORA_RESHARE_WITH_EXTRA_PROPERTIES, "alice@example.org")
        assert len(entities) == 1
        entity = entities[0]
        assert isinstance(entity, DiasporaReshare)
        assert entity.raw_content == "Important note here"
        assert entity.entity_type == "Comment"

    @patch("federation.entities.activitypub.mappers.logger.error")
    def test_invalid_entity_logs_an_error(self, mock_logger):
        entities = message_to_objects(ACTIVITYPUB_PROFILE_INVALID, "http://example.com/1234")
        assert len(entities) == 0
        assert mock_logger.called

    def test_adds_source_protocol_to_entity(self):
        entities = message_to_objects(ACTIVITYPUB_PROFILE, "http://example.com/1234")
        assert entities[0]._source_protocol == "activitypub"

    def test_source_object(self):
        entities = message_to_objects(ACTIVITYPUB_PROFILE, "http://example.com/1234")
        entity = entities[0]
        assert entity._source_object == ACTIVITYPUB_PROFILE

    @pytest.mark.skip
    def test_element_to_objects_calls_retrieve_remote_profile(self, mock_retrieve, mock_validate):
        message_to_objects(DIASPORA_POST_COMMENT, "alice@alice.diaspora.example.org")
        mock_retrieve.assert_called_once_with("alice@alice.diaspora.example.org")

    @pytest.mark.skip
    def test_element_to_objects_verifies_handles_are_the_same(self, mock_check):
        message_to_objects(DIASPORA_POST_SIMPLE, "bob@example.org")
        mock_check.assert_called_once_with("bob@example.org", "alice@alice.diaspora.example.org")

    @pytest.mark.skip
    def test_element_to_objects_returns_no_entity_if_handles_are_different(self):
        entities = message_to_objects(DIASPORA_POST_SIMPLE, "bob@example.org")
        assert not entities


class TestGetOutboundEntity:
    def test_already_fine_entities_are_returned_as_is(self, private_key):
        entity = ActivitypubAccept()
        assert get_outbound_entity(entity, private_key) == entity
        entity = ActivitypubFollow()
        assert get_outbound_entity(entity, private_key) == entity
        entity = ActivitypubProfile()
        assert get_outbound_entity(entity, private_key) == entity

    def test_accept_is_converted_to_activitypubaccept(self, private_key):
        entity = Accept()
        assert isinstance(get_outbound_entity(entity, private_key), ActivitypubAccept)

    def test_follow_is_converted_to_activitypubfollow(self, private_key):
        entity = Follow()
        assert isinstance(get_outbound_entity(entity, private_key), ActivitypubFollow)

    def test_profile_is_converted_to_activitypubprofile(self, private_key):
        entity = Profile()
        assert isinstance(get_outbound_entity(entity, private_key), ActivitypubProfile)
