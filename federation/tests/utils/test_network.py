from datetime import timedelta
from unittest.mock import DEFAULT, patch, AsyncMock, MagicMock, Mock, call

import aiohttp
import pytest
from requests import HTTPError
from requests.exceptions import SSLError, RequestException

from federation.utils.network import (
    fetch_document, USER_AGENT, send_document, fetch_host_ip
)


class TestFetchDocument:
    call_args = {"headers": {'user-agent': USER_AGENT}}
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.text.return_value = "bla"

    @patch.object(aiohttp.ClientSession, "get")
    async def test_extra_headers(self, mock_get):
        mock_get.__aenter__.return_value = self.mock_response
        await fetch_document("https://example.com/foo", extra_headers={'accept': 'application/activity+json'})
        mock_get.assert_called_once_with('https://example.com/foo', headers={
            'user-agent': USER_AGENT, 'accept': 'application/activity+json'})

    async def test_raises_without_url_and_host(self):
        with pytest.raises(ValueError):
            await fetch_document()

    @patch.object(aiohttp.ClientSession, "get")
    async def test_url_is_called(self, mock_get):
        mock_get.__aenter__.return_value = self.mock_response
        await fetch_document("https://localhost")
        assert mock_get.called

    @patch.object(aiohttp.ClientSession, "get")
    async def test_host_is_called_with_https_first_then_http(self, mock_get):
        def mock_failing_https_get(url, *args, **kwargs):
            if url.find("https://") > -1:
                raise aiohttp.ClientResponseError(None, None)
            return self.mock_response
        mock_get.side_effect = mock_failing_https_get
        mock_get.__aenter__.return_value = self.mock_response
        await fetch_document(host="localhost")
        assert mock_get.call_count == 2
        assert mock_get.call_args_list == [
            call("https://localhost/", **self.call_args),
            call("http://localhost/", **self.call_args),
        ]

    @patch.object(aiohttp.ClientSession, "get")
    async def test_host_is_sanitized(self, mock_get):
        mock_get.__aenter__.return_value = self.mock_response
        await fetch_document(host="http://localhost")
        assert mock_get.call_args_list == [
            call("https://localhost/", **self.call_args)
        ]

    @patch.object(aiohttp.ClientSession, "get")
    async def test_path_is_sanitized(self, mock_get):
        mock_get.__aenter__.return_value = self.mock_response
        await fetch_document(host="localhost", path="foobar/bazfoo")
        assert mock_get.call_args_list == [
            call("https://localhost/foobar/bazfoo", **self.call_args)
        ]

    @patch.object(aiohttp.ClientSession, "get")
    async def test_exception_is_raised_if_both_protocols_fail(self, mock_get):
        mock_get.side_effect = aiohttp.ClientConnectionError
        doc, code, exc = await fetch_document(host="localhost")
        assert mock_get.call_count == 2
        assert doc == None
        assert code == None
        assert exc.__class__ == aiohttp.ClientConnectionError

    @patch.object(aiohttp.ClientSession, "get")
    async def test_exception_is_raised_if_url_fails(self, mock_get):
        mock_get.side_effect = aiohttp.ClientConnectionError
        doc, code, exc = await fetch_document("localhost")
        assert mock_get.call_count == 1
        assert doc == None
        assert code == None
        assert exc.__class__ == aiohttp.ClientConnectionError

    @patch.object(aiohttp.ClientSession, "get")
    async def test_exception_is_raised_if_http_fails_and_raise_ssl_errors_true(self, mock_get):
        mock_get.side_effect = aiohttp.ClientSSLError(None, OSError)
        doc, code, exc = await fetch_document("localhost")
        assert mock_get.call_count == 1
        assert doc == None
        assert code == None
        assert exc.__class__ == aiohttp.ClientSSLError

    @patch.object(aiohttp.ClientSession, "get")
    async def test_exception_is_raised_on_network_error(self, mock_get):
        mock_get.side_effect = aiohttp.ClientError
        doc, code, exc = await fetch_document(host="localhost")
        assert mock_get.call_count == 1
        assert doc == None
        assert code == None
        assert exc.__class__ == aiohttp.ClientError


class TestFetchHostIp:
    @patch('federation.utils.network.socket.gethostbyname', autospec=True, return_value='127.0.0.1')
    def test_calls(self, mock_get_ip):
        result = fetch_host_ip('domain.local')
        assert result == '127.0.0.1'
        mock_get_ip.assert_called_once_with('domain.local')


async def mock_resp(*args, **kwargs):
    return await AsyncMock(status=200)


class TestSendDocument:
    call_args = {"headers": {'user-agent': USER_AGENT}}
    mock_response = AsyncMock()
    mock_response.status = 200

    @patch.object(aiohttp.ClientSession, "post", new_callable=AsyncMock)
    async def test_post_is_called(self, mock_post):
        mock_post.return_value = self.mock_response
        code, exc = await send_document("http://localhost", {"foo": "bar"})
        print(dir(mock_post.return_value))
        mock_post.assert_called_once_with(
            "http://localhost", data={"foo": "bar"}, **self.call_args
        )
        assert code == 200
        assert exc == None

    @patch.object(aiohttp.ClientSession, "post", side_effect=aiohttp.ClientResponseError(None, None))
    async def test_post_raises_and_returns_exception(self, mock_post):
        code, exc = await send_document("http://localhost", {"foo": "bar"})
        assert code == None
        assert exc.__class__ == aiohttp.ClientResponseError

    @patch.object(aiohttp.ClientSession, "post", new_callable=AsyncMock)
    async def test_post_called_with_only_one_headers_kwarg(self, mock_post):
        # A failure might raise:
        # TypeError: MagicMock object got multiple values for keyword argument 'headers'
        mock_post.return_value = self.mock_response
        await send_document("http://localhost", {"foo": "bar"}, **self.call_args)
        mock_post.assert_called_once_with(
            "http://localhost", data={"foo": "bar"}, **self.call_args
        )

    @patch.object(aiohttp.ClientSession, "post", new_callable=AsyncMock)
    async def test_headers_in_either_case_are_handled_without_exception(self, mock_post):
        mock_post.return_value = self.mock_response
        await send_document("http://localhost", {"foo": "bar"}, **self.call_args)
        mock_post.assert_called_once_with(
            "http://localhost", data={"foo": "bar"}, headers={'user-agent': USER_AGENT}
        )
        mock_post.reset_mock()
        await send_document("http://localhost", {"foo": "bar"}, headers={'User-Agent': USER_AGENT})
        mock_post.assert_called_once_with(
            "http://localhost", data={"foo": "bar"}, headers={'User-Agent': USER_AGENT}
        )
