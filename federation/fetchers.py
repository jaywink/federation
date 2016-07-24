# -*- coding: utf-8 -*-
import importlib
import warnings


def retrieve_remote_profile(handle, protocol=None):
    """High level retrieve profile method.

    Retrieve the profile from a remote location, using either the given protocol or by checking each
    protocol until a user can be constructed from the remote documents.

    Currently, due to no other protocols supported, always use the Diaspora protocol.

    Args:
        handle (str) - The profile handle in format username@domain.tld
    """
    if protocol:
        warnings.warn("Currently retrieve_remote_profile doesn't use the protocol argument. Diaspora protocol"
                      "will always be used.")
    protocol_name = "diaspora"
    utils = importlib.import_module("federation.utils.%s" % protocol_name)
    return utils.retrieve_and_parse_profile(handle)
