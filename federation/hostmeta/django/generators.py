import logging

from django.http import HttpResponseBadRequest, JsonResponse, HttpResponseNotFound

from federation.hostmeta.generators import RFC3033Webfinger, generate_nodeinfo2_document
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


def rfc3033_webfinger_view(request, *args, **kwargs):
    """
    Django view to generate an RFC3033 webfinger.
    """
    resource = request.GET.get("resource")
    if not resource:
        return HttpResponseBadRequest("No resource found")
    if not resource.startswith("acct:"):
        return HttpResponseBadRequest("Invalid resource")

    handle = resource.replace("acct:", "")
    profile_func = get_function_from_config("get_profile_function")

    try:
        profile = profile_func(handle=handle, request=request)
    except Exception as exc:
        logger.warning("rfc3033_webfinger_view - Failed to get profile by handle %s: %s", handle, exc)
        return HttpResponseNotFound()

    # TODO: remove this hotfix that is made to fix webfinger for diaspora in activitypub branch
    profile = profile.as_protocol("diaspora")

    config = get_configuration()
    webfinger = RFC3033Webfinger(
        id=profile.id,
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
