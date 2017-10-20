import importlib


def retrieve_remote_content(entity_class, id, sender_key_fetcher=None):
    """Retrieve remote content and return an Entity object.

    Currently, due to no other protocols supported, always use the Diaspora protocol.

    :param entity_class: Federation entity class (from ``federation.entity.base``).
    :param id: ID of the remote entity, in format``guid@domain.tld``.
    :param sender_key_fetcher: Function to use to fetch sender public key. If not given, network will be used
        to fetch the profile and the key. Function must take handle as only parameter and return a public key.
    :returns: Entity class instance or ``None``
    """
    protocol_name = "diaspora"
    utils = importlib.import_module("federation.utils.%s" % protocol_name)
    return utils.retrieve_and_parse_content(entity_class, id, sender_key_fetcher=sender_key_fetcher)


def retrieve_remote_profile(handle):
    """High level retrieve profile method.

    Retrieve the profile from a remote location, using either the given protocol or by checking each
    protocol until a user can be constructed from the remote documents.

    Currently, due to no other protocols supported, always use the Diaspora protocol.

    :param handle: The profile handle in format username@domain.tld
    :returns: ``federation.entities.base.Profile`` or ``None``
    """
    protocol_name = "diaspora"
    utils = importlib.import_module("federation.utils.%s" % protocol_name)
    return utils.retrieve_and_parse_profile(handle)
