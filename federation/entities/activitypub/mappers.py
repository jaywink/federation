from typing import List, Callable, Dict, Union

from federation.entities.activitypub.entities import ActivitypubFollow, ActivitypubProfile, ActivitypubAccept
from federation.entities.base import Follow, Profile, Accept
from federation.entities.mixins import BaseEntity
from federation.types import UserType

MAPPINGS = {
    "Accept": ActivitypubAccept,
    "Follow": ActivitypubFollow,
    "Person": ActivitypubProfile,
}


def element_to_objects(
        payload: Dict, sender: str, sender_key_fetcher:Callable[[str], str]=None, user: UserType =None,
) -> List:
    """
    Transform an Element to a list of entities recursively.
    """
    entities = []
    cls = MAPPINGS.get(payload.get('type'))
    if not cls:
        return []

    transformed = transform_attributes(payload, cls)
    entity = cls(**transformed)

    if hasattr(entity, "post_receive"):
        entity.post_receive(transformed)

    entities.append(entity)

    return entities


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
    if cls in [ActivitypubAccept, ActivitypubFollow, ActivitypubProfile]:
        # Already fine
        outbound = entity
    elif cls == Accept:
        outbound = ActivitypubAccept.from_base(entity)
    elif cls == Follow:
        outbound = ActivitypubFollow.from_base(entity)
    elif cls == Profile:
        outbound = ActivitypubProfile.from_base(entity)
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
    return outbound


def message_to_objects(
        message: Dict, sender: str, sender_key_fetcher: Callable[[str], str] = None, user: UserType = None,
) -> List:
    """
    Takes in a message extracted by a protocol and maps it to entities.
    """
    # We only really expect one element here for ActivityPub.
    return element_to_objects(message, sender, sender_key_fetcher, user)


def transform_attribute(key: str, value: Union[str, Dict, int], transformed: Dict, cls) -> None:
    if value is None:
        value = ""
    if key == "id":
        if cls == ActivitypubProfile:
            transformed["id"] = value
        else:
            transformed["activity_id"] = value
    elif key == "actor":
        transformed["actor_id"] = value
    elif key == "inboxes" and isinstance(value, dict):
        if "inboxes" not in transformed:
            transformed["inboxes"] = {"private": None, "public": None}
        transformed["endpoints"]["public"] = value.get("sharedInbox")
    elif key == "icon":
        # TODO maybe we should ditch these size constants and instead have a more flexible dict for images
        # so based on protocol there would either be one url or many by size name
        if isinstance(value, dict):
            transformed["image_urls"] = {
                "small": value['url'],
                "medium": value['url'],
                "large": value['url'],
            }
        else:
            transformed["image_urls"] = {
                "small": value,
                "medium": value,
                "large": value,
            }
    elif key == "inbox":
        if "inboxes" not in transformed:
            transformed["inboxes"] = {"private": None, "public": None}
        transformed["inboxes"]["private"] = value
    elif key == "name":
        transformed["name"] = value
    elif key == "object":
        if isinstance(value, dict):
            transform_attributes(value, cls, transformed)
        else:
            transformed["target_id"] = value
    elif key == "preferredUsername":
        transformed["username"] = value
    elif key == "publicKey":
        transformed["public_key"] = value.get('publicKeyPem', '')
    elif key == "summary":
        transformed["raw_content"] = value
    elif key == "url":
        transformed["url"] = value


def transform_attributes(payload: Dict, cls, transformed: Dict = None) -> Dict:
    if not transformed:
        transformed = {}
    for key, value in payload.items():
        transform_attribute(key, value, transformed, cls)
    return transformed
