import inspect


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
