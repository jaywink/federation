import json
from unittest.mock import patch, AsyncMock

import pytest
from django.http import HttpResponse
from django.test import RequestFactory
from django.utils.decorators import method_decorator
from django.views import View

from federation.entities.activitypub.django.views import ActivitypubObjectView
from federation.tests.fixtures.entities import activitypubprofile


async def dummy_get_object_function(request, signer=None):
    if request.method == 'GET':
        return False
    return True


class TestActivityPubObjectView:
    async def test_returns_bad_request_if_not_right_content_type(self):
        request = RequestFactory().get("/")
        view = ActivitypubObjectView.as_view()
        response = await view(request=request)

        assert response.status_code == 400

    @patch("federation.entities.activitypub.django.views.get_function_from_config", return_value=dummy_get_object_function)
    async def test_receives_messages_to_inbox(self, mock_function):
        request = RequestFactory().post("/u/bla/inbox/", data='{"foo": "bar"}', content_type="application/json")
        view = ActivitypubObjectView.as_view()
        response = await view(request=request)

        assert response.status_code == 202

    @pytest.mark.parametrize('content_type', (
            'application/json', 'application/activity+json', 'application/ld+json',
            'application/ld+json; profile="https://www.w3.org/ns/activitystreams"',
            'application/activity+json, application/ld+json',
    ))
    @patch("federation.entities.activitypub.django.views.get_function_from_config")
    async def test_renders_as2(self, mock_function, content_type, activitypubprofile):
        async def get_object(x, y):
            return activitypubprofile
        mock_function.return_value = get_object
        request = RequestFactory().get("/", HTTP_ACCEPT=content_type)
        view = ActivitypubObjectView.as_view()
        response = await view(request=request)

        assert response.status_code == 200
        content = json.loads(response.content)
        assert content['name'] == 'Bob Bobertson'
        assert response['Content-Type'] == 'application/activity+json'

    @patch("federation.entities.activitypub.django.views.get_function_from_config")
    async def test_restricted_view__denied_when_not_authorized(self, mock_function):
        async def get_object(x, y):
            return None
        mock_function.return_value = get_object
        request = RequestFactory().get("/", HTTP_ACCEPT='application/activity+json')
        view = ActivitypubObjectView.as_view()
        with patch("federation.tests.django.utils.get_object_function", new=dummy_get_object_function):
            response = await view(request=request)

        assert response.status_code == 404
