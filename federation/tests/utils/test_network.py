# -*- coding: utf-8 -*-
from unittest.mock import patch, Mock, call

import pytest
from requests import HTTPError
from requests.exceptions import SSLError, RequestException

from federation.utils.network import fetch_document, USER_AGENT


class TestFetchDocument(object):
    call_args = {"timeout": 10, "headers": {'user-agent': USER_AGENT}}

    def test_raises_without_url_and_host(self):
        with pytest.raises(ValueError):
            fetch_document()

    @patch("federation.utils.network.requests.get")
    def test_url_is_called(self, mock_get):
        mock_get.return_value = Mock(status_code=200, text="foo")
        fetch_document("https://localhost")
        assert mock_get.called

    @patch("federation.utils.network.requests.get")
    def test_host_is_called_with_https_first_then_http(self, mock_get):
        def mock_failing_https_get(url, *args, **kwargs):
            if url.find("https://") > -1:
                raise HTTPError()
            return Mock(status_code=200, text="foo")
        mock_get.side_effect = mock_failing_https_get
        fetch_document(host="localhost")
        assert mock_get.call_count == 2
        assert mock_get.call_args_list == [
            call("https://localhost/", **self.call_args),
            call("http://localhost/", **self.call_args),
        ]

    @patch("federation.utils.network.requests.get")
    def test_host_is_sanitized(self, mock_get):
        mock_get.return_value = Mock(status_code=200, text="foo")
        fetch_document(host="http://localhost")
        assert mock_get.call_args_list == [
            call("https://localhost/", **self.call_args)
        ]

    @patch("federation.utils.network.requests.get")
    def test_path_is_sanitized(self, mock_get):
        mock_get.return_value = Mock(status_code=200, text="foo")
        fetch_document(host="localhost", path="foobar/bazfoo")
        assert mock_get.call_args_list == [
            call("https://localhost/foobar/bazfoo", **self.call_args)
        ]

    @patch("federation.utils.network.requests.get")
    def test_exception_is_raised_if_both_protocols_fail(self, mock_get):
        mock_get.side_effect = HTTPError
        doc, code, exc = fetch_document(host="localhost")
        assert mock_get.call_count == 2
        assert doc == None
        assert code == None
        assert exc.__class__ == HTTPError

    @patch("federation.utils.network.requests.get")
    def test_exception_is_raised_if_url_fails(self, mock_get):
        mock_get.side_effect = HTTPError
        doc, code, exc = fetch_document("localhost")
        assert mock_get.call_count == 1
        assert doc == None
        assert code == None
        assert exc.__class__ == HTTPError

    @patch("federation.utils.network.requests.get")
    def test_exception_is_raised_if_http_fails_and_raise_ssl_errors_true(self, mock_get):
        mock_get.side_effect = SSLError
        doc, code, exc = fetch_document("localhost")
        assert mock_get.call_count == 1
        assert doc == None
        assert code == None
        assert exc.__class__ == SSLError

    @patch("federation.utils.network.requests.get")
    def test_exception_is_raised_on_network_error(self, mock_get):
        mock_get.side_effect = RequestException
        doc, code, exc = fetch_document(host="localhost")
        assert mock_get.call_count == 1
        assert doc == None
        assert code == None
        assert exc.__class__ == RequestException
