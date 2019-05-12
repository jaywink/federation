from unittest.mock import patch, Mock, call

import pytest
from requests import HTTPError
from requests.exceptions import SSLError, RequestException

from federation.utils.network import (
    fetch_document, USER_AGENT, send_document, fetch_country_by_ip, fetch_host_ip_and_country, fetch_host_ip)


@patch('federation.utils.network.ipdata', autospec=True)
class TestFetchCountryByIp:
    def test_calls_ip_api_endpoint(self, mock_ipdata):
        mock_lookup = Mock(lookup=Mock(return_value={'status': 200, 'response': {'country_code': 'DE'}}))
        mock_ipdata.IPData.return_value = mock_lookup
        country = fetch_country_by_ip('127.0.0.1')
        mock_lookup.lookup.assert_called_once_with('127.0.0.1')
        assert country == 'DE'


class TestFetchDocument:
    call_args = {"timeout": 10, "headers": {'user-agent': USER_AGENT}}

    @patch("federation.utils.network.requests.get", autospec=True, return_value=Mock(status_code=200, text="foo"))
    def test_extra_headers(self, mock_get):
        fetch_document("https://example.com/foo", extra_headers={'accept': 'application/activity+json'})
        mock_get.assert_called_once_with('https://example.com/foo', headers={
            'user-agent': USER_AGENT, 'accept': 'application/activity+json',
        })

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


class TestFetchHostIp:
    @patch('federation.utils.network.socket.gethostbyname', autospec=True, return_value='127.0.0.1')
    def test_calls(self, mock_get_ip):
        result = fetch_host_ip('domain.local')
        assert result == '127.0.0.1'
        mock_get_ip.assert_called_once_with('domain.local')


class TestFetchHostIpAndCountry:
    @patch('federation.utils.network.fetch_country_by_ip', autospec=True, return_value='FI')
    @patch('federation.utils.network.fetch_host_ip', autospec=True, return_value='127.0.0.1')
    def test_calls(self, mock_get_ip, mock_fetch_country):
        result = fetch_host_ip_and_country('domain.local')
        assert result == ('127.0.0.1', 'FI')
        mock_get_ip.assert_called_once_with('domain.local')
        mock_fetch_country.assert_called_once_with('127.0.0.1')


class TestSendDocument:
    call_args = {"timeout": 10, "headers": {'user-agent': USER_AGENT}}

    @patch("federation.utils.network.requests.post", return_value=Mock(status_code=200))
    def test_post_is_called(self, mock_post):
        code, exc = send_document("http://localhost", {"foo": "bar"})
        mock_post.assert_called_once_with(
            "http://localhost", data={"foo": "bar"}, **self.call_args
        )
        assert code == 200
        assert exc == None

    @patch("federation.utils.network.requests.post", side_effect=RequestException)
    def test_post_raises_and_returns_exception(self, mock_post):
        code, exc = send_document("http://localhost", {"foo": "bar"})
        assert code == None
        assert exc.__class__ == RequestException

    @patch("federation.utils.network.requests.post", return_value=Mock(status_code=200))
    def test_post_called_with_only_one_headers_kwarg(self, mock_post):
        # A failure might raise:
        # TypeError: MagicMock object got multiple values for keyword argument 'headers'
        send_document("http://localhost", {"foo": "bar"}, **self.call_args)
        mock_post.assert_called_once_with(
            "http://localhost", data={"foo": "bar"}, **self.call_args
        )

    @patch("federation.utils.network.requests.post", return_value=Mock(status_code=200))
    def test_headers_in_either_case_are_handled_without_exception(self, mock_post):
        send_document("http://localhost", {"foo": "bar"}, **self.call_args)
        mock_post.assert_called_once_with(
            "http://localhost", data={"foo": "bar"}, headers={'user-agent': USER_AGENT}, timeout=10
        )
        mock_post.reset_mock()
        send_document("http://localhost", {"foo": "bar"}, headers={'User-Agent': USER_AGENT})
        mock_post.assert_called_once_with(
            "http://localhost", data={"foo": "bar"}, headers={'User-Agent': USER_AGENT}, timeout=10
        )
