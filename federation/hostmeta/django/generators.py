import logging

# noinspection PyPackageRequirements
from django.http import HttpResponseBadRequest, JsonResponse, HttpResponseNotFound

from federation.hostmeta.generators import (
    RFC7033Webfinger, generate_nodeinfo2_document, MatrixClientWellKnown, MatrixServerWellKnown,
)
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


def matrix_client_wellknown_view(request, *args, **kwargs):
    try:
        matrix_config_func = get_function_from_config("matrix_config_function")
    except AttributeError:
        return HttpResponseBadRequest("Not configured")
    matrix_config = matrix_config_func()

    wellknown = MatrixClientWellKnown(
        homeserver_base_url=matrix_config["homeserver_base_url"],
        identity_server_base_url=matrix_config.get("identity_server_base_url"),
        other_keys=matrix_config.get("client_wellknown_other_keys"),
    )
    return JsonResponse(wellknown.render())


def matrix_server_wellknown_view(request, *args, **kwargs):
    try:
        matrix_config_func = get_function_from_config("matrix_config_function")
    except AttributeError:
        return HttpResponseBadRequest("Not configured")
    matrix_config = matrix_config_func()

    wellknown = MatrixServerWellKnown(
        homeserver_domain_with_port=matrix_config["homeserver_domain_with_port"],
    )
    return JsonResponse(wellknown.render())


def rfc7033_webfinger_view(request, *args, **kwargs):
    """
    Django view to generate an RFC7033 webfinger.
    """
    resource = request.GET.get("resource")
    kwargs = {}
    if not resource:
        return HttpResponseBadRequest("No resource found")
    if resource.startswith("acct:"):
        kwargs['handle'] = resource.replace("acct:", "").lower()
    elif resource.startswith("http"):
        kwargs['fid'] = resource
    else:
        return HttpResponseBadRequest("Invalid resource")
    kwargs['request'] = request
    logger.debug("%s requested with %s", kwargs)
    profile_func = get_function_from_config("get_profile_function")

    try:
        profile = profile_func(**kwargs)
    except Exception as exc:
        logger.warning("rfc7033_webfinger_view - Failed to get profile from resource %s: %s", resource, exc)
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
