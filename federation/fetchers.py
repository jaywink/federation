import importlib
import logging

logger = logging.getLogger("federation")


def retrieve_remote_content(id, sender_key_fetcher=None):
    """Retrieve remote content and return an Entity object.

    Currently, due to no other protocols supported, always use the Diaspora protocol.

    :param id: ID of the remote entity.
    :param sender_key_fetcher: Function to use to fetch sender public key. If not given, network will be used
        to fetch the profile and the key. Function must take handle as only parameter and return a public key.
    :returns: Entity class instance or ``None``
    """
    protocol_name = "diaspora"
    utils = importlib.import_module("federation.utils.%s" % protocol_name)
    return utils.retrieve_and_parse_content(id, sender_key_fetcher=sender_key_fetcher)


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
    if not handle.islower():
        logger.warning("retrieve_remote_profile - Handle is not lower case! Will use lower case version to continue.")
    return utils.retrieve_and_parse_profile(handle.lower())
