from datetime import timedelta
import json
from unittest.mock import patch, Mock

import pytest

from federation.entities.activitypub.models import Follow, Note
from federation.tests.fixtures.payloads import (
    ACTIVITYPUB_FOLLOW, ACTIVITYPUB_POST, ACTIVITYPUB_POST_OBJECT, ACTIVITYPUB_POST_OBJECT_IMAGES)
from federation.utils.activitypub import (
    retrieve_and_parse_document, retrieve_and_parse_profile, get_profile_id_from_webfinger)


class TestGetProfileIdFromWebfinger:
    @patch("federation.utils.activitypub.try_retrieve_webfinger_document", autospec=True, return_value=None)
    def test_calls_try_retrieve_webfinger_document(self, mock_try):
        get_profile_id_from_webfinger("foobar@localhost")
        mock_try.assert_called_once_with("foobar@localhost")

    @patch("federation.utils.activitypub.try_retrieve_webfinger_document", autospec=True, return_value=json.dumps({
        "links": [
            {
                "rel": "foobar",
                "type": "application/activity+json",
                "href": "spam and eggs",
            },
            {
                "rel": "self",
                "type": "application/activity+json",
                "href": "https://localhost/profile",
            },
        ],
    }))
    def test_returns_href_from_document(self, mock_try):
        href = get_profile_id_from_webfinger("foobar@localhost")
        assert href == "https://localhost/profile"

    @patch("federation.utils.activitypub.try_retrieve_webfinger_document", autospec=True, return_value="not json")
    def test_survives_bad_json(self, mock_try):
        href = get_profile_id_from_webfinger("foobar@localhost")
        assert href is None


class TestRetrieveAndParseDocument:
    @patch("federation.utils.activitypub.fetch_document", autospec=True, return_value=(None, None, None))
    def test_calls_fetch_document(self, mock_fetch):
        retrieve_and_parse_document("https://example.com/foobar")
        # auth argument is passed with kwargs
        auth = mock_fetch.call_args.kwargs.get('auth', None)
        mock_fetch.assert_called_once_with(
            "https://example.com/foobar", extra_headers={'accept': 'application/activity+json'}, cache=True, auth=auth,
        )

    @patch("federation.entities.activitypub.models.extract_receivers", return_value=[])
    @patch("federation.utils.activitypub.fetch_document", autospec=True, return_value=(
        json.dumps(ACTIVITYPUB_FOLLOW), None, None),
    )
    @patch.object(Follow, "post_receive")
    def test_returns_entity_for_valid_document__follow(self, mock_post_receive, mock_fetch, mock_recv):
        entity = retrieve_and_parse_document("https://example.com/foobar")
        assert isinstance(entity, Follow)

    @patch("federation.entities.activitypub.models.get_profile_or_entity", return_value=None)
    @patch("federation.utils.activitypub.fetch_document", autospec=True, return_value=(
            json.dumps(ACTIVITYPUB_POST_OBJECT), None, None),
    )
    def test_returns_entity_for_valid_document__post__without_activity(self, mock_fetch, mock_recv):
        entity = retrieve_and_parse_document("https://example.com/foobar")
        assert isinstance(entity, Note)

    @patch("federation.entities.activitypub.models.extract_receivers", return_value=[])
    @patch("federation.utils.activitypub.fetch_document", autospec=True, return_value=(
            json.dumps(ACTIVITYPUB_POST_OBJECT_IMAGES), None, None),
    )
    def test_returns_entity_for_valid_document__post__without_activity__with_images(self, mock_fetch, mock_recv):
        entity = retrieve_and_parse_document("https://example.com/foobar")
        assert isinstance(entity, Note)
        assert len(entity._children) == 1
        assert entity._children[0].url == "https://files.mastodon.social/media_attachments/files/017/792/237/original" \
                                          "/foobar.jpg"

    @patch("federation.entities.activitypub.models.verify_ld_signature", return_value=None)
    @patch("federation.entities.activitypub.models.get_profile_or_entity", return_value=None)
    @patch("federation.utils.activitypub.fetch_document", autospec=True, return_value=(
        json.dumps(ACTIVITYPUB_POST), None, None),
    )
    def test_returns_entity_for_valid_document__post__wrapped_in_activity(
            self, mock_fetch, mock_recv, mock_sign):
        entity = retrieve_and_parse_document("https://example.com/foobar")
        assert isinstance(entity, Note)

    @patch("federation.utils.activitypub.fetch_document", autospec=True, return_value=('{"foo": "bar"}', None, None))
    def test_returns_none_for_invalid_document(self, mock_fetch):
        entity = retrieve_and_parse_document("https://example.com/foobar")
        assert entity is None


class TestRetrieveAndParseProfile:
    @patch("federation.utils.activitypub.get_profile_id_from_webfinger", autospec=True, return_value=None)
    def test_calls_get_profile_id_from_webfinger__with_handle_fid(self, mock_get):
        retrieve_and_parse_profile("profile@example.com")
        mock_get.assert_called_once_with("profile@example.com")

    @patch("federation.utils.activitypub.retrieve_and_parse_document", autospec=True)
    def test_calls_retrieve_and_parse_document__with_url_fid(self, mock_retrieve):
        retrieve_and_parse_profile("https://example.com/profile")
        mock_retrieve.assert_called_once_with("https://example.com/profile")

    @patch("federation.utils.activitypub.fetch_document", autospec=True, return_value=('{"foo": "bar"}', None, None))
    def test_returns_none_on_invalid_document(self, mock_fetch):
        profile = retrieve_and_parse_profile("https://example.com/profile")
        assert profile is None

    @patch("federation.utils.activitypub.retrieve_and_parse_document", autospec=True)
    def test_calls_profile_validate(self, mock_retrieve):
        mock_profile = Mock()
        mock_retrieve.return_value = mock_profile
        retrieve_and_parse_profile("https://example.com/profile")
        assert mock_profile.validate.called
