import json

import pytest
from django.http import HttpResponse
from django.test import RequestFactory
from django.utils.decorators import method_decorator
from django.views import View

from federation.entities.activitypub.django.views import activitypub_object_view


@activitypub_object_view
def dummy_view(request, *args, **kwargs):
    return HttpResponse("foo")


@method_decorator(activitypub_object_view, name='get')
class DummyView(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse("foo")


class TestActivityPubObjectView:
    @pytest.mark.parametrize('content_type', (
            'application/json', 'application/activity+json', 'application/ld+json',
            'application/ld+json; profile="https://www.w3.org/ns/activitystreams"',
    ))
    def test_renders_as2(self, content_type):
        request = RequestFactory().get("/", HTTP_ACCEPT=content_type)
        response = dummy_view(request=request)

        assert response.status_code == 200
        content = json.loads(response.content)
        assert content['name'] == 'Bob Bobértson'
        assert response['Content-Type'] == 'application/activity+json'

    @pytest.mark.parametrize('content_type', (
            'application/json', 'application/activity+json', 'application/ld+json',
            'application/ld+json; profile="https://www.w3.org/ns/activitystreams"',
    ))
    def test_renders_as2__cbv(self, content_type):
        request = RequestFactory().get("/", HTTP_ACCEPT=content_type)
        view = DummyView.as_view()
        response = view(request=request)

        assert response.status_code == 200
        content = json.loads(response.content)
        assert content['name'] == 'Bob Bobértson'
        assert response['Content-Type'] == 'application/activity+json'

    def test_falls_back_if_not_right_content_type(self):
        request = RequestFactory().get("/")
        response = dummy_view(request=request)

        assert response.content == b'foo'

    def test_falls_back_if_not_right_content_type__cbv(self):
        request = RequestFactory().get("/")
        view = DummyView.as_view()
        response = view(request=request)

        assert response.content == b'foo'
