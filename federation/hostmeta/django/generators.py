import importlib
import logging

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseBadRequest, JsonResponse, HttpResponseNotFound

from federation.hostmeta.generators import RFC3033Webfinger, generate_nodeinfo2_document

logger = logging.getLogger("federation")


def get_configuration():
    """
    Combine defaults with the Django configuration.
    """
    configuration = {
        "hcard_path": "/hcard/users/",
        "nodeinfo2_function": None,
        "search_path": None,
    }
    configuration.update(settings.FEDERATION)
    if not all([
        "get_profile_function" in configuration,
        "base_url" in configuration,
    ]):
        raise ImproperlyConfigured("Missing required FEDERATION settings, please check documentation.")
    return configuration


def get_function_from_config(item):
    """
    Import the function to get profile by handle.
    """
    config = get_configuration()
    func_path = config.get(item)
    module_path, func_name = func_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    func = getattr(module, func_name)
    return func


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
        profile = profile_func(handle)
    except Exception as exc:
        logger.warning("rfc3033_webfinger_view - Failed to get profile by handle %s: %s", handle, exc)
        return HttpResponseNotFound()

    config = get_configuration()
    webfinger = RFC3033Webfinger(
        id=profile.get('id'),
        base_url=config.get('base_url'),
        profile_path=profile.get('profile_path'),
        hcard_path=config.get('hcard_path'),
        atom_path=profile.get('atom_path'),
        search_path=config.get('search_path'),
    )

    return JsonResponse(
        webfinger.render(),
        content_type="application/jrd+json",
    )
