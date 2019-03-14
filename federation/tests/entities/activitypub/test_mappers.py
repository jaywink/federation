import pytest

from federation.entities.activitypub.entities import ActivitypubFollow
from federation.entities.activitypub.mappers import message_to_objects
from federation.tests.fixtures.payloads import ACTIVITYPUB_FOLLOW, ACTIVITYPUB_PROFILE


class TestActivitypubEntityMappersReceive:
    def test_message_to_objects__follow(self):
        entities = message_to_objects(ACTIVITYPUB_FOLLOW, "https://example.com/actor")
        assert len(entities) == 1
        entity = entities[0]
        assert isinstance(entity, ActivitypubFollow)
        assert entity.actor_id == "https://example.com/actor"
        assert entity.target_id == "https://example.org/actor"
        assert entity.following is True

    @pytest.mark.skip
    def test_message_to_objects_mentions_are_extracted(self):
        entities = message_to_objects(
            DIASPORA_POST_SIMPLE_WITH_MENTION, "alice@alice.diaspora.example.org"
        )
        assert len(entities) == 1
        post = entities[0]
        assert post._mentions == {'jaywink@jasonrobinson.me'}

    @pytest.mark.skip
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

    @pytest.mark.skip
    def test_message_to_objects_post_with_photos(self):
        entities = message_to_objects(DIASPORA_POST_WITH_PHOTOS, "alice@alice.diaspora.example.org")
        assert len(entities) == 1
        post = entities[0]
        assert isinstance(post, DiasporaPost)
        photo = post._children[0]
        assert isinstance(photo, DiasporaImage)
        assert photo.remote_path == "https://alice.diaspora.example.org/uploads/images/"
        assert photo.remote_name == "1234.jpg"
        assert photo.raw_content == ""
        assert photo.linked_type == "Post"
        assert photo.linked_guid == "((guidguidguidguidguidguidguid))"
        assert photo.height == 120
        assert photo.width == 120
        assert photo.guid == "((guidguidguidguidguidguidguif))"
        assert photo.handle == "alice@alice.diaspora.example.org"
        assert photo.public == False
        assert photo.created_at == datetime(2011, 7, 20, 1, 36, 7)

    @pytest.mark.skip
    def test_message_to_objects_comment(self, mock_validate):
        entities = message_to_objects(DIASPORA_POST_COMMENT, "alice@alice.diaspora.example.org",
                                      sender_key_fetcher=Mock())
        assert len(entities) == 1
        comment = entities[0]
        assert isinstance(comment, DiasporaComment)
        assert isinstance(comment, Comment)
        assert comment.target_guid == "((parent_guidparent_guidparent_guidparent_guid))"
        assert comment.guid == "((guidguidguidguidguidguid))"
        assert comment.handle == "alice@alice.diaspora.example.org"
        assert comment.participation == "comment"
        assert comment.raw_content == "((text))"
        assert comment.signature == "((signature))"
        assert comment._xml_tags == [
            "guid", "parent_guid", "text", "author",
        ]
        mock_validate.assert_called_once_with()

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

    @pytest.mark.skip
    def test_message_to_objects_receiving_actor_id_is_saved(self):
        # noinspection PyTypeChecker
        entities = message_to_objects(
            DIASPORA_POST_SIMPLE,
            "alice@alice.diaspora.example.org",
            user=Mock(id="bob@example.com")
        )
        entity = entities[0]
        assert entity._receiving_actor_id == "bob@example.com"

    @pytest.mark.skip
    def test_message_to_objects_retraction(self):
        entities = message_to_objects(DIASPORA_RETRACTION, "bob@example.com")
        assert len(entities) == 1
        entity = entities[0]
        assert isinstance(entity, DiasporaRetraction)
        assert entity.handle == "bob@example.com"
        assert entity.target_guid == "x" * 16
        assert entity.entity_type == "Post"

    @pytest.mark.skip
    def test_message_to_objects_accounce(self):
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

    @pytest.mark.skip
    def test_message_to_objects_reshare_extra_properties(self):
        entities = message_to_objects(DIASPORA_RESHARE_WITH_EXTRA_PROPERTIES, "alice@example.org")
        assert len(entities) == 1
        entity = entities[0]
        assert isinstance(entity, DiasporaReshare)
        assert entity.raw_content == "Important note here"
        assert entity.entity_type == "Comment"

    @pytest.mark.skip
    def test_invalid_entity_logs_an_error(self, mock_logger):
        entities = message_to_objects(DIASPORA_POST_INVALID, "alice@alice.diaspora.example.org")
        assert len(entities) == 0
        assert mock_logger.called

    @pytest.mark.skip
    def test_adds_source_protocol_to_entity(self):
        entities = message_to_objects(DIASPORA_POST_SIMPLE, "alice@alice.diaspora.example.org")
        assert entities[0]._source_protocol == "diaspora"

    @pytest.mark.skip
    def test_source_object(self, mock_validate):
        entities = message_to_objects(DIASPORA_POST_COMMENT, "alice@alice.diaspora.example.org",
                                      sender_key_fetcher=Mock())
        entity = entities[0]
        assert entity._source_object == etree.tostring(etree.fromstring(DIASPORA_POST_COMMENT))

    @pytest.mark.skip
    def test_element_to_objects_calls_sender_key_fetcher(self, mock_validate):
        mock_fetcher = Mock()
        message_to_objects(DIASPORA_POST_COMMENT, "alice@alice.diaspora.example.org", mock_fetcher)
        mock_fetcher.assert_called_once_with(
            "alice@alice.diaspora.example.org",
        )

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


@pytest.mark.skip
class TestGetOutboundEntity:
    def test_already_fine_entities_are_returned_as_is(self, private_key):
        entity = DiasporaPost()
        assert get_outbound_entity(entity, private_key) == entity
        entity = DiasporaLike()
        assert get_outbound_entity(entity, private_key) == entity
        entity = DiasporaComment()
        assert get_outbound_entity(entity, private_key) == entity
        entity = DiasporaProfile()
        assert get_outbound_entity(entity, private_key) == entity
        entity = DiasporaContact()
        assert get_outbound_entity(entity, private_key) == entity
        entity = DiasporaReshare()
        assert get_outbound_entity(entity, private_key) == entity

    def test_post_is_converted_to_diasporapost(self, private_key):
        entity = Post()
        assert isinstance(get_outbound_entity(entity, private_key), DiasporaPost)

    def test_comment_is_converted_to_diasporacomment(self, private_key):
        entity = Comment()
        assert isinstance(get_outbound_entity(entity, private_key), DiasporaComment)

    def test_reaction_of_like_is_converted_to_diasporalike(self, private_key):
        entity = Reaction(reaction="like")
        assert isinstance(get_outbound_entity(entity, private_key), DiasporaLike)


    def test_profile_is_converted_to_diasporaprofile(self, private_key):
        entity = Profile()
        assert isinstance(get_outbound_entity(entity, private_key), DiasporaProfile)

    def test_other_reaction_raises(self, private_key):
        entity = Reaction(reaction="foo")
        with pytest.raises(ValueError):
            get_outbound_entity(entity, private_key)

    def test_other_relation_raises(self, private_key):
        entity = Relationship(relationship="foo")
        with pytest.raises(ValueError):
            get_outbound_entity(entity, private_key)

    def test_retraction_is_converted_to_diasporaretraction(self, private_key):
        entity = Retraction()
        assert isinstance(get_outbound_entity(entity, private_key), DiasporaRetraction)

    def test_follow_is_converted_to_diasporacontact(self, private_key):
        entity = Follow()
        assert isinstance(get_outbound_entity(entity, private_key), DiasporaContact)

    def test_share_is_converted_to_diasporareshare(self, private_key):
        entity = Share()
        assert isinstance(get_outbound_entity(entity, private_key), DiasporaReshare)

    def test_signs_relayable_if_no_signature(self, private_key):
        entity = DiasporaComment()
        outbound = get_outbound_entity(entity, private_key)
        assert outbound.signature != ""

    def test_returns_entity_if_outbound_doc_on_entity(self, private_key):
        entity = Comment()
        entity.outbound_doc = "foobar"
        assert get_outbound_entity(entity, private_key) == entity


@pytest.mark.skip
def test_check_sender_and_entity_handle_match():
    assert not check_sender_and_entity_handle_match("foo", "bar")
    assert check_sender_and_entity_handle_match("foo", "foo")
