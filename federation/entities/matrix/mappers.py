import logging

from federation.entities.base import Profile, Post
from federation.entities.matrix.entities import MatrixRoomMessage, MatrixProfile
from federation.entities.mixins import BaseEntity

logger = logging.getLogger("federation")


def get_outbound_entity(entity: BaseEntity, private_key):
    """Get the correct outbound entity for this protocol.

    :arg entity: An entity instance which can be of a base or protocol entity class.
    :arg private_key: Private key of sender in str format
    :returns: Protocol specific entity class instance.
    :raises ValueError: If conversion cannot be done.
    """
    if getattr(entity, "outbound_doc", None):
        # If the entity already has an outbound doc, just return the entity as is
        return entity
    outbound = None
    cls = entity.__class__
    if cls in [
        MatrixProfile,
        MatrixRoomMessage,
    ]:
        # Already fine
        outbound = entity
    elif cls == Post:
        outbound = MatrixRoomMessage.from_base(entity)
    elif cls == Profile:
        outbound = MatrixProfile.from_base(entity)
    if not outbound:
        raise ValueError("Don't know how to convert this base entity to Matrix protocol entities.")
    if hasattr(outbound, "pre_send"):
        outbound.pre_send()
    # Validate the entity
    outbound.validate(direction="outbound")
    return outbound
