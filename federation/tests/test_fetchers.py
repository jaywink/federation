from unittest.mock import patch, Mock

from federation.fetchers import retrieve_remote_profile, retrieve_remote_content


class TestRetrieveRemoteContent:
    @patch("federation.fetchers.importlib.import_module")
    def test_calls_diaspora_retrieve_and_parse_content(self, mock_import):
        mock_retrieve = Mock()
        mock_import.return_value = mock_retrieve
        retrieve_remote_content("diaspora://user@example.com/status_message/1234", sender_key_fetcher=sum)
        mock_retrieve.retrieve_and_parse_content.assert_called_once_with(
            "diaspora://user@example.com/status_message/1234", sender_key_fetcher=sum,
        )


class TestRetrieveRemoteProfile:
    @patch("federation.fetchers.importlib.import_module")
    def test_calls_diaspora_retrieve_and_parse_profile(self, mock_import):
        mock_retrieve = Mock()
        mock_import.return_value = mock_retrieve
        retrieve_remote_profile("diaspora://user@example.com/profile/1234")
        mock_retrieve.retrieve_and_parse_profile.assert_called_once_with("user@example.com")

    @patch("federation.fetchers.importlib.import_module")
    def test_calls_diaspora_retrieve_and_parse_profile__lower_cases_handle_when_needed(self, mock_import):
        mock_retrieve = Mock()
        mock_import.return_value = mock_retrieve
        retrieve_remote_profile("diaspora://uSer@ExamPle.com/profile/1234")
        mock_retrieve.retrieve_and_parse_profile.assert_called_once_with("user@example.com")
