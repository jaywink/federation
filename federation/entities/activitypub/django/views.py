from typing import Callable

from django.http import HttpRequest, Http404, JsonResponse


def activitypub_object_view(request: HttpRequest, fetch_function: Callable, fallback_view=None):
    # TODO implement as view decorator instead?
    """
    Generic ActivityPub object view.

    Takes an ID and fetches it using the provided function. Renders the ActivityPub object
    in JSON if the object is found. Falls back to fallback view, if given, if the content
    type doesn't match.
    """
    if request.content_type != 'application/json':
        return fallback_view.as_view(request=request)
    obj = fetch_function(request.build_absolute_uri())
    if not obj:
        raise Http404

    return JsonResponse(obj.to_as2())
