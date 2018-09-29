from functools import wraps

from django.http import Http404, JsonResponse

from federation.utils.django import get_function_from_config


def activitypub_object_view(request, *args, **kwargs):
    """
    Generic ActivityPub object view decorator.

    Takes an ID and fetches it using the provided function. Renders the ActivityPub object
    in JSON if the object is found. Falls back to decorated view, if the content
    type doesn't match.
    """
    def decorator(func):
        @wraps(func)
        def inner(request, *args, **kwargs):
            if request.content_type != 'application/json':
                return func(request, *args, **kwargs)
            get_object_function = get_function_from_config('get_object_function')
            obj = get_object_function(request.build_absolute_uri())
            if not obj:
                raise Http404

            as2_obj = obj.as_protocol('activitypub')
            return JsonResponse(as2_obj.to_as2())
        return inner
    return decorator
