from unittest.mock import patch, Mock, call

from federation.fetchers import retrieve_remote_profile, retrieve_remote_content


class TestRetrieveRemoteContent:
    @patch("federation.fetchers.importlib.import_module")
    def test_calls_activitypub_retrieve_and_parse_content(self, mock_import):
        mock_retrieve = Mock()
        mock_import.return_value = mock_retrieve
        retrieve_remote_content("https://example.com/foobar")
        mock_retrieve.retrieve_and_parse_content.assert_called_once_with(
            id="https://example.com/foobar", guid=None, handle=None, entity_type=None, cache=True, sender_key_fetcher=None,
        )

    @patch("federation.fetchers.importlib.import_module")
    def test_calls_diaspora_retrieve_and_parse_content(self, mock_import):
        mock_retrieve = Mock()
        mock_import.return_value = mock_retrieve
        retrieve_remote_content("1234", handle="user@example.com", entity_type="post", sender_key_fetcher=sum)
        mock_retrieve.retrieve_and_parse_content.assert_called_once_with(
            id="1234", guid="1234", handle="user@example.com", entity_type="post", cache=True, sender_key_fetcher=sum,
        )


class TestRetrieveRemoteProfile:
    @patch("federation.fetchers.importlib.import_module", autospec=True)
    @patch("federation.fetchers.validate_handle", autospec=True, return_value=False)
    @patch("federation.fetchers.identify_protocol_by_id", autospec=True, return_value=Mock(PROTOCOL_NAME='activitypub'))
    def test_retrieve_remote_profile__url_calls_activitypub_retrieve(self, mock_identify, mock_validate, mock_import):
        mock_utils = Mock()
        mock_import.return_value = mock_utils
        retrieve_remote_profile("https://example.com/foo")
        mock_import.assert_called_once_with("federation.utils.activitypub")
        mock_utils.retrieve_and_parse_profile.assert_called_once_with("https://example.com/foo")

    @patch("federation.fetchers.importlib.import_module", autospec=True)
    @patch("federation.fetchers.validate_handle", autospec=True, return_value=True)
    @patch("federation.fetchers.identify_protocol_by_id", autospec=True)
    def test_retrieve_remote_profile__handle_calls_both_activitypub_and_diaspora_retrieve(
            self, mock_identify, mock_validate, mock_import,
    ):
        mock_utils = Mock(retrieve_and_parse_profile=Mock(return_value=None))
        mock_import.return_value = mock_utils
        retrieve_remote_profile("user@example.com")
        calls = [
            call("federation.utils.activitypub"),
            call("federation.utils.diaspora"),
        ]
        assert mock_import.call_args_list == calls
        calls = [
            call("user@example.com"),
            call("user@example.com"),
        ]
        assert mock_utils.retrieve_and_parse_profile.call_args_list == calls
