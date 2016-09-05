# -*- coding: utf-8 -*-
from federation.entities.diaspora.mappers import get_outbound_entity
from federation.protocols.diaspora.protocol import Protocol


def handle_create_payload(entity, from_user, to_user=None):
    """Create a payload with the correct protocol.

    Since we don't know the protocol, we need to first query the recipient. However, for a PoC implementation,
    supporting only Diaspora, we're going to assume that for now.

    Args:
        entity (obj)        - Entity object to send
        from_user (obj)     - User sending the object
        to_user (obj)       - Contact entry to send to (required for non-public content)

    `from_user` must have `private_key` and `handle` attributes.
    `to_user` must have `key` attribute.
    """
    # Just use Diaspora protocol for now
    protocol = Protocol()
    outbound_entity = get_outbound_entity(entity)
    data = protocol.build_send(entity=outbound_entity, from_user=from_user, to_user=to_user)
    return data
