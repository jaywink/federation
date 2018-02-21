import json
from unittest.mock import patch, Mock

from django.test import RequestFactory

from federation.hostmeta.django import rfc3033_webfinger_view
from federation.hostmeta.django.generators import get_profile_func


def test_get_profile_func():
    func = get_profile_func()
    assert callable(func)


class TestRFC3033WebfingerView:
    def test_no_resource_returns_bad_request(self):
        request = RequestFactory().get("/.well-known/webfinger")
        response = rfc3033_webfinger_view(request)
        assert response.status_code == 400

    def test_invalid_resource_returns_bad_request(self):
        request = RequestFactory().get("/.well-known/webfinger?resource=foobar")
        response = rfc3033_webfinger_view(request)
        assert response.status_code == 400

    @patch("federation.hostmeta.django.generators.get_profile_func")
    def test_unknown_handle_returns_not_found(self, mock_get_func):
        mock_get_func.return_value = Mock(side_effect=Exception)
        request = RequestFactory().get("/.well-known/webfinger?resource=acct:foobar@domain.tld")
        response = rfc3033_webfinger_view(request)
        assert response.status_code == 404

    def test_rendered_webfinger_returned(self):
        request = RequestFactory().get("/.well-known/webfinger?resource=acct:foobar@example.com")
        response = rfc3033_webfinger_view(request)
        assert response.status_code == 200
        assert response['Content-Type'] == "application/jrd+json"
        assert json.loads(response.content.decode("utf-8")) == {
            "subject": "acct:foobar@example.com",
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
                    "rel": "http://schemas.google.com/g/2010#updates-from",
                    "type": "application/atom+xml",
                    "href": "https://example.com/profile/1234/atom.xml",
                },
            ],
        }
