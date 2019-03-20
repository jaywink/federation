from unittest.mock import patch

from Crypto.PublicKey.RSA import RsaKey

from federation.entities.activitypub.constants import (
    CONTEXTS_DEFAULT, CONTEXT_MANUALLY_APPROVES_FOLLOWERS, CONTEXT_LD_SIGNATURES, CONTEXT_HASHTAG, CONTEXT_SENSITIVE)
from federation.entities.activitypub.entities import ActivitypubProfile, ActivitypubAccept
from federation.types import UserType


class TestEntitiesConvertToAS2:
    def test_accept_to_as2(self, activitypubaccept):
        result = activitypubaccept.to_as2()
        assert result == {
            "@context": CONTEXTS_DEFAULT,
            "id": "https://localhost/accept",
            "type": "Accept",
            "actor": "https://localhost/profile",
            "object": "https://example.com/follow/1234",
        }

    def test_post_to_as2(self, activitypubpost):
        # TODO expand
        result = activitypubpost.to_as2()
        assert result.get('@context') == CONTEXTS_DEFAULT + [
            CONTEXT_HASHTAG,
            CONTEXT_SENSITIVE,
        ]
        assert result.get('type') == 'Note'

    def test_profile_to_as2(self):
        # TODO expand
        entity = ActivitypubProfile(
            handle="bob@example.com", raw_content="foobar", name="Bob Bobertson", public=True,
            tag_list=["socialfederation", "federation"], image_urls={
                "large": "urllarge", "medium": "urlmedium", "small": "urlsmall"
            }
        )
        result = entity.to_as2()
        assert result.get('@context') == CONTEXTS_DEFAULT + [
            CONTEXT_LD_SIGNATURES,
            CONTEXT_MANUALLY_APPROVES_FOLLOWERS,
        ]
        assert result.get('type') == 'Person'


class TestEntitiesPostReceive:
    @patch("federation.utils.activitypub.retrieve_and_parse_profile", autospec=True)
    @patch("federation.entities.activitypub.entities.handle_send", autospec=True)
    def test_follow_post_receive__sends_correct_accept_back(
            self, mock_send, mock_retrieve, activitypubfollow, profile
    ):
        mock_retrieve.return_value = profile
        activitypubfollow.post_receive()
        args, kwargs = mock_send.call_args_list[0]
        assert isinstance(args[0], ActivitypubAccept)
        assert args[0].activity_id.startswith("https://example.com/profile#accept-")
        assert args[0].actor_id == "https://example.com/profile"
        assert args[0].target_id == "https://localhost/follow"
        assert isinstance(args[1], UserType)
        assert args[1].id == "https://example.com/profile"
        assert isinstance(args[1].private_key, RsaKey)
        assert kwargs['recipients'] == [{
            "fid": "https://example.com/private",
            "protocol": "activitypub",
            "public": False,
        }]
