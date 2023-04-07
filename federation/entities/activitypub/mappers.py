import logging
from typing import List, Callable, Dict, Union, Optional

from federation.entities.activitypub.models import element_to_objects
from federation.entities.base import Follow, Profile, Accept, Post, Comment, Retraction, Share, Image, Collection
from federation.entities.mixins import BaseEntity
from federation.types import UserType, ReceiverVariant
import federation.entities.activitypub.models as models

logger = logging.getLogger("federation")


def get_outbound_entity(entity: BaseEntity, private_key):
    """Get the correct outbound entity for this protocol.

    We might have to look at entity values to decide the correct outbound entity.
    If we cannot find one, we should raise as conversion cannot be guaranteed to the given protocol.

    Private key of author is needed to be passed for signing the outbound entity.

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
        models.Accept, models.Follow, models.Person, models.Note,
        models.Delete, models.Tombstone, models.Announce, models.Collection,
        models.OrderedCollection,
        ] and isinstance(entity, BaseEntity):
        # Already fine
        outbound = entity
    elif cls == Accept:
        outbound = models.Accept.from_base(entity)
    elif cls == Follow:
        outbound = models.Follow.from_base(entity)
    elif cls == Post:
        outbound = models.Post.from_base(entity)
    elif cls == Comment:
        outbound = models.Comment.from_base(entity)
    elif cls == Profile:
        outbound = models.Person.from_base(entity)
    elif cls == Retraction:
        if entity.entity_type in ('Post', 'Comment'):
            outbound = models.Tombstone.from_base(entity)
            outbound.activity = models.Delete
        elif entity.entity_type == 'Share':
            outbound = models.Announce.from_base(entity)
            outbound.activity = models.Undo
            outbound._required.remove('id')
        elif entity.entity_type == 'Profile':
            outbound = models.Delete.from_base(entity)
    elif cls == Share:
        outbound = models.Announce.from_base(entity)
    elif cls == Collection:
        outbound = models.OrderedCollection.from_base(entity) if entity.ordered else models.Collection.from_base(entity)
    if not outbound:
        raise ValueError("Don't know how to convert this base entity to ActivityPub protocol entities.")
    # TODO LDS signing
    # if isinstance(outbound, DiasporaRelayableMixin) and not outbound.signature:
    #     # Sign by author if not signed yet. We don't want to overwrite any existing signature in the case
    #     # that this is being sent by the parent author
    #     outbound.sign(private_key)
    #     # If missing, also add same signature to `parent_author_signature`. This is required at the moment
    #     # in all situations but is apparently being removed.
    #     # TODO: remove this once Diaspora removes the extra signature
    #     outbound.parent_signature = outbound.signature
    if hasattr(outbound, "pre_send"):
        outbound.pre_send()
    # Validate the entity
    outbound.validate(direction="outbound")
    return outbound


def message_to_objects(
        message: Dict, sender: str = "", sender_key_fetcher: Callable[[str], str] = None, user: UserType = None,
) -> List:
    """
    Takes in a message extracted by a protocol and maps it to entities.
    """
    # We only really expect one element here for ActivityPub.
    return element_to_objects(message, sender)


