import json

from django.http import HttpResponse
from django.test import RequestFactory

from federation.entities.activitypub.django.views import activitypub_object_view
from federation.entities.activitypub.entities import ActivitypubProfile


@activitypub_object_view
def dummy_view(request, *args, **kwargs):
    return HttpResponse("foo")


class TestActivityPubObjectView:
    def test_renders_as2(self):
        # TODO test with real content type, but also json
        request = RequestFactory().get("/", CONTENT_TYPE='application/json')
        response = dummy_view(request)(request=request)

        assert response.status_code == 200
        content = json.loads(response.content)
        assert content['name'] == 'Bob Bobértson'
        # TODO verify content type

    def test_falls_back_if_not_right_content_type(self):
        # TODO
        pass

    def test_falls_back_to_fallback_view(self):
        # TODO
        pass
