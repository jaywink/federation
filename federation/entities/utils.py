import inspect
from typing import Optional


def get_base_attributes(entity):
    """Build a dict of attributes of an entity.

    Returns attributes and their values, ignoring any properties, functions and anything that starts
    with an underscore.
    """
    attributes = {}
    cls = entity.__class__
    for attr, _ in inspect.getmembers(cls, lambda o: not isinstance(o, property) and not inspect.isroutine(o)):
        if not attr.startswith("_"):
            attributes[attr] = getattr(entity, attr)
    return attributes


def get_name_for_profile(fid: str) -> Optional[str]:
    """
    Get a profile display name from a profile via the configured profile getter.

    Currently only works with Django configuration.
    """
    try:
        from federation.utils.django import get_function_from_config
        profile_func = get_function_from_config("get_profile_function")
        if not profile_func:
            return
        profile = profile_func(fid)
        if not profile:
            return
        if profile.name == fid and profile.username:
            return profile.username
        else:
            return profile.name
    except ImportError:
        pass
