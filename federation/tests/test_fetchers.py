# -*- coding: utf-8 -*-
from unittest.mock import patch, Mock

from federation.fetchers import retrieve_remote_profile


class TestRetrieveRemoteProfile(object):
    @patch("federation.fetchers.importlib.import_module")
    def test_calls_diaspora_retrieve_and_parse_profile(self, mock_import):
        class MockRetrieve(Mock):
            def retrieve_and_parse_profile(self, handle):
                return "called with %s" % handle

        mock_retrieve = MockRetrieve()
        mock_import.return_value = mock_retrieve
        assert retrieve_remote_profile("foo@bar") == "called with foo@bar"
