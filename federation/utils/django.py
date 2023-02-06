import importlib
import redis
from requests_cache import RedisCache, SQLiteCache

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from federation.types import UserType


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
        "tags_path": None,
        # TODO remove or default to True once AP support is more ready
        "activitypub": False,
    }
    try:
        configuration.update(settings.FEDERATION)
    except (ModuleNotFoundError, ImproperlyConfigured):
        # Django is not properly configured, return defaults
        return configuration
    if not all([
        "get_private_key_function" in configuration,
        "get_profile_function" in configuration,
        "base_url" in configuration,
        "federation_id" in configuration,
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

def get_federation_user():
    config = get_configuration()
    if not config.get('federation_id'): return None

    try:
        get_key = get_function_from_config("get_private_key_function")
    except AttributeError:
        return None

    key = get_key(config['federation_id'])
    if not key: return None

    return UserType(id=config['federation_id'], private_key=key)

def get_redis():
    """
    Returns a connected redis object if available
    """
    config = get_configuration()
    if not config.get('redis'): return None

    return redis.Redis(**config['redis'])

def get_requests_cache_backend(namespace):
    """
    Use RedisCache is available, else fallback to SQLiteCache
    """
    config = get_configuration()
    if not config.get('redis'): return SQLiteCache()

    return RedisCache(namespace, **config['redis'])
