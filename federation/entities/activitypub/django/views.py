from django.http import JsonResponse, HttpResponse, HttpResponseNotFound

from federation.entities.activitypub.mappers import get_outbound_entity
from federation.utils.django import get_function_from_config


def activitypub_object_view(func):
    """
    Generic ActivityPub object view decorator.

    Takes an ID and fetches it using the provided function. Renders the ActivityPub object
    in JSON if the object is found. Falls back to decorated view, if the content
    type doesn't match.
    """

    def inner(request, *args, **kwargs):

        def get(request, *args, **kwargs):
            fallback = True
            accept = request.META.get('HTTP_ACCEPT', '')
            for content_type in (
                    'application/json', 'application/activity+json', 'application/ld+json',
            ):
                if accept.find(content_type) > -1:
                    fallback = False
                    break
            if fallback:
                return func(request, *args, **kwargs)

            get_object_function = get_function_from_config('get_object_function')
            obj = get_object_function(request)
            if not obj:
                return HttpResponseNotFound()

            as2_obj = get_outbound_entity(obj, None)
            return JsonResponse(as2_obj.to_as2(), content_type='application/activity+json')

        def post(request, *args, **kwargs):
            process_payload_function = get_function_from_config('process_payload_function')
            result = process_payload_function(request)
            if result:
                return JsonResponse({}, content_type='application/json', status=202)
            else:
                return JsonResponse({"result": "error"}, content_type='application/json', status=400)

        if request.method == 'GET':
            return get(request, *args, **kwargs)
        elif request.method == 'POST' and request.path.endswith('/inbox/'):
            return post(request, *args, **kwargs)

        return HttpResponse(status=405)
    return inner
