from cryptography.exceptions import InvalidSignature
from django.http import JsonResponse, HttpResponse, HttpResponseNotFound
from requests_http_signature import HTTPSignatureHeaderAuth

from federation.entities.activitypub.mappers import get_outbound_entity
from federation.protocols.activitypub.signing import verify_request_signature
from federation.types import RequestType
from federation.utils.django import get_function_from_config


def get_and_verify_signer(request):
    """
    A remote user might be allowed to access retricted content
    if a valid signature is provided.

    Only done for content.
    """
    # TODO: revisit this when we start responding to sending follow[ing,ers] collections
    if request.path.startswith('/u/'): return None 
    get_public_key = get_function_from_config('get_public_key_function')
    if not request.headers.get('Signature'): return None
    req = RequestType(
            url=request.build_absolute_uri(),
            body=request.body,
            method=request.method,
            headers=request.headers)
    try:
        return verify_request_signature(req)
    except ValueError:
        return None


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
            obj = get_object_function(request, get_and_verify_signer(request))
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
        elif request.method == 'POST' and request.path.startswith('/u/') and request.path.endswith('/inbox/'):
            return post(request, *args, **kwargs)

        return HttpResponse(status=405)
    return inner
