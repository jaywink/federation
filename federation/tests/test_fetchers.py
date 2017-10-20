from unittest.mock import patch, Mock

from federation.entities.base import Post
from federation.fetchers import retrieve_remote_profile, retrieve_remote_content


class TestRetrieveRemoteContent:
    @patch("federation.fetchers.importlib.import_module")
    def test_calls_diaspora_retrieve_and_parse_content(self, mock_import):
        mock_retrieve = Mock()
        mock_import.return_value = mock_retrieve
        retrieve_remote_content(Post, "1234@example.com", sender_key_fetcher=sum)
        mock_retrieve.retrieve_and_parse_content.assert_called_once_with(
            Post, "1234@example.com", sender_key_fetcher=sum,
        )


class TestRetrieveRemoteProfile:
    @patch("federation.fetchers.importlib.import_module")
    def test_calls_diaspora_retrieve_and_parse_profile(self, mock_import):
        mock_retrieve = Mock()
        mock_import.return_value = mock_retrieve
        retrieve_remote_profile("foo@bar")
        mock_retrieve.retrieve_and_parse_profile.assert_called_once_with("foo@bar")
