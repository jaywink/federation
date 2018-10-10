import importlib

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def get_configuration():
    """
    Combine defaults with the Django configuration.
    """
    configuration = {
        "get_object_function": None,
        "hcard_path": "/hcard/users/",
        "nodeinfo2_function": None,
        "process_payload_function": None,
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
