from asgiref.sync import sync_to_async
from cryptography.exceptions import InvalidSignature
from django.http import JsonResponse, HttpResponse, HttpResponseNotFound
from django.views import View

from federation.entities.activitypub.mappers import get_outbound_entity
from federation.protocols.activitypub.protocol import Protocol
from federation.types import RequestType
from federation.utils.django import get_function_from_config


async def get_and_verify_signer(request):
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
    protocol = Protocol(request=req,  get_contact_key=get_public_key)
    try:
        await protocol.verify()
        return protocol.sender
    except (ValueError, KeyError, InvalidSignature) as exc:
        return None


class ActivitypubObjectView(View):
    """
    Generic ActivityPub object view.

    Takes an ID and fetches it using the provided function. Renders the ActivityPub object
    in JSON if the object is found. Returns http 400 on bad content-type
    """

    async def get(self, request, *args, **kwargs):
        fallback = True
        accept = request.META.get('HTTP_ACCEPT', '')
        for content_type in (
                'application/json', 'application/activity+json', 'application/ld+json',
        ):
            if accept.find(content_type) > -1:
                fallback = False
                break
        if fallback:
            return JsonResponse({"result": "bad request content-type"}, content_type='application/json', status=400)

        get_object_function = get_function_from_config('get_object_function')
        obj = await get_object_function(request, get_and_verify_signer(request))
        if not obj:
            return HttpResponseNotFound()
        
        as2_obj = await get_outbound_entity(obj, None)
        return JsonResponse(as2_obj.to_as2(), content_type='application/activity+json')

    async def post(self, request, *args, **kwargs):
        process_payload_function = get_function_from_config('process_payload_function')
        result = await sync_to_async(process_payload_function)(request)
        if result:
            return JsonResponse({}, content_type='application/json', status=202)
        else:
            return JsonResponse({"result": "error"}, content_type='application/json', status=400)
