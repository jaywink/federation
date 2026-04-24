import json
from unittest.mock import patch, AsyncMock, Mock

from django.test import AsyncRequestFactory

from federation.hostmeta.django import rfc7033_webfinger_view
from federation.hostmeta.django.generators import nodeinfo2_view
from federation.utils.django import get_function_from_config
from federation.tests.fixtures.hostmeta import NODEINFO2_10_DOC


def test_get_function_from_config():
    func = get_function_from_config("get_profile_function")
    assert callable(func)


class TestNodeInfo2View:
    async def test_returns_400_if_not_configured(self):
        request = AsyncRequestFactory().get('/.well-known/x-nodeinfo2')
        response = await nodeinfo2_view(request)
        assert response.status_code == 400

    @patch("federation.hostmeta.django.generators.get_function_from_config")
    async def test_returns_200(self, mock_get_func):
        mock_get_func.return_value = AsyncMock(return_value=json.loads(NODEINFO2_10_DOC))
        request = AsyncRequestFactory().get('/.well-known/x-nodeinfo2')
        response = await nodeinfo2_view(request)
        assert response.status_code == 200


class TestRFC7033WebfingerView:
    @patch("federation.hostmeta.django.generators.get_function_from_config")
    async def test_handle_lowercased(self, mock_get_func):
        mock_get_profile = AsyncMock(side_effect=Exception)
        mock_get_func.return_value = mock_get_profile
        request = AsyncRequestFactory().get("/.well-known/webfinger?resource=acct:Foobar@example.com")
        try:
            await rfc7033_webfinger_view(request)
        except Exception:
            pass
        mock_get_profile.assert_called_once_with(handle='foobar@example.com', request=request)

    async def test_no_resource_returns_bad_request(self):
        request = AsyncRequestFactory().get("/.well-known/webfinger")
        response = await rfc7033_webfinger_view(request)
        assert response.status_code == 400

    async def test_invalid_resource_returns_bad_request(self):
        request = AsyncRequestFactory().get("/.well-known/webfinger?resource=foobar")
        response = await rfc7033_webfinger_view(request)
        assert response.status_code == 400

    @patch("federation.hostmeta.django.generators.get_function_from_config")
    async def test_unknown_handle_returns_not_found(self, mock_get_func):
        mock_get_func.return_value = AsyncMock(side_effect=Exception)
        request = AsyncRequestFactory().get("/.well-known/webfinger?resource=acct:foobar@domain.tld")
        response = await rfc7033_webfinger_view(request)
        assert response.status_code == 404

    async def test_rendered_webfinger_returned(self):
        request = AsyncRequestFactory().get("/.well-known/webfinger?resource=acct:foobar@example.com")
        response = await rfc7033_webfinger_view(request)
        assert response.status_code == 200
        assert response['Content-Type'] == "application/jrd+json"
        assert json.loads(response.content.decode("utf-8")) == {
            "subject": "acct:foobar@example.com",
            "aliases": [
                "https://example.com/profile/1234/",
                "https://example.com/p/1234/",
            ],
            "links": [
                {
                    "rel": "http://microformats.org/profile/hcard",
                    "type": "text/html",
                    "href": "https://example.com/hcard/users/1234",
                },
                {
                    "rel": "http://joindiaspora.com/seed_location",
                    "type": "text/html",
                    "href": "https://example.com",
                },
                {
                    "rel": "http://webfinger.net/rel/profile-page",
                    "type": "text/html",
                    "href": "https://example.com/profile/1234/",
                },
                {
                    "rel": "salmon",
                    "href": "https://example.com/receive/users/1234",
                },
                {
                    "rel": "self",
                    "href": "https://example.com/p/1234/",
                    "type": "application/activity+json",
                },
                {
                    "rel": "http://schemas.google.com/g/2010#updates-from",
                    "type": "application/atom+xml",
                    "href": "https://example.com/profile/1234/atom.xml",
                },
                {
                    "rel": "http://ostatus.org/schema/1.0/subscribe",
                    "template": "https://example.com/search?q={uri}",
                },
            ],
        }
