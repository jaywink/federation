import logging

from django.http import HttpResponseBadRequest, JsonResponse, HttpResponseNotFound

from federation.hostmeta.generators import RFC7033Webfinger, generate_nodeinfo2_document
from federation.utils.django import get_configuration, get_function_from_config
from federation.utils.text import get_path_from_url

logger = logging.getLogger("federation")


def nodeinfo2_view(request, *args, **kwargs):
    try:
        nodeinfo2_func = get_function_from_config("nodeinfo2_function")
    except AttributeError:
        return HttpResponseBadRequest("Not configured")
    nodeinfo2 = nodeinfo2_func()

    return JsonResponse(generate_nodeinfo2_document(**nodeinfo2))


def rfc7033_webfinger_view(request, *args, **kwargs):
    """
    Django view to generate an RFC7033 webfinger.
    """
    resource = request.GET.get("resource")
    if not resource:
        return HttpResponseBadRequest("No resource found")
    if not resource.startswith("acct:"):
        return HttpResponseBadRequest("Invalid resource")
    handle = resource.replace("acct:", "").lower()
    logger.debug(f"{handle} requested with {request}")
    profile_func = get_function_from_config("get_profile_function")

    try:
        profile = profile_func(handle=handle, request=request)
    except Exception as exc:
        logger.warning("rfc7033_webfinger_view - Failed to get profile by handle %s: %s", handle, exc)
        return HttpResponseNotFound()

    config = get_configuration()
    webfinger = RFC7033Webfinger(
        id=profile.id,
        handle=profile.handle,
        guid=profile.guid,
        base_url=config.get('base_url'),
        profile_path=get_path_from_url(profile.url),
        hcard_path=config.get('hcard_path'),
        atom_path=get_path_from_url(profile.atom_url),
        search_path=config.get('search_path'),
    )

    return JsonResponse(
        webfinger.render(),
        content_type="application/jrd+json",
    )
