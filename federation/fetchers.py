# -*- coding: utf-8 -*-
import importlib


def retrieve_remote_profile(handle):
    """High level retrieve profile method.

    Retrieve the profile from a remote location, using either the given protocol or by checking each
    protocol until a user can be constructed from the remote documents.

    Currently, due to no other protocols supported, always use the Diaspora protocol.

    :arg handle: The profile handle in format username@domain.tld
    :returns: ``federation.entities.base.Profile`` or ``None``
    """
    protocol_name = "diaspora"
    utils = importlib.import_module("federation.utils.%s" % protocol_name)
    return utils.retrieve_and_parse_profile(handle)
