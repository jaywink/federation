from unittest.mock import patch, Mock

from federation.fetchers import retrieve_remote_profile, retrieve_remote_content


class TestRetrieveRemoteContent:
    @patch("federation.fetchers.importlib.import_module")
    def test_calls_diaspora_retrieve_and_parse_content(self, mock_import):
        mock_retrieve = Mock()
        mock_import.return_value = mock_retrieve
        retrieve_remote_content("1234", handle="user@example.com", entity_type="post", sender_key_fetcher=sum)
        mock_retrieve.retrieve_and_parse_content.assert_called_once_with(
            guid="1234", handle="user@example.com", entity_type="post", sender_key_fetcher=sum,
        )


class TestRetrieveRemoteProfile:
    @patch("federation.fetchers.importlib.import_module", autospec=True)
    @patch("federation.fetchers.identify_protocol_by_id", autospec=True, return_value=Mock(PROTOCOL_NAME='activitypub'))
    def test_calls_activitypub_retrieve_and_parse_profile(self, mock_identify, mock_import):
        mock_utils = Mock()
        mock_import.return_value = mock_utils
        retrieve_remote_profile("https://example.com/foo")
        mock_import.assert_called_once_with("federation.utils.activitypub")
        mock_utils.retrieve_and_parse_profile.assert_called_once_with("https://example.com/foo")

    @patch("federation.fetchers.importlib.import_module", autospec=True)
    @patch("federation.fetchers.identify_protocol_by_id", autospec=True, return_value=Mock(PROTOCOL_NAME='diaspora'))
    def test_calls_diaspora_retrieve_and_parse_profile(self, mock_identify, mock_import):
        mock_utils = Mock()
        mock_import.return_value = mock_utils
        retrieve_remote_profile("user@example.com")
        mock_import.assert_called_once_with("federation.utils.diaspora")
        mock_utils.retrieve_and_parse_profile.assert_called_once_with("user@example.com")
