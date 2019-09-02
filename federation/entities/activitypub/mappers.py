import logging
from typing import List, Callable, Dict, Union, Optional

from markdownify import markdownify

from federation.entities.activitypub.constants import NAMESPACE_PUBLIC
from federation.entities.activitypub.entities import (
    ActivitypubFollow, ActivitypubProfile, ActivitypubAccept, ActivitypubPost, ActivitypubComment,
    ActivitypubRetraction, ActivitypubShare)
from federation.entities.activitypub.objects import IMAGE_TYPES
from federation.entities.base import Follow, Profile, Accept, Post, Comment, Retraction, Share, Image
from federation.entities.mixins import BaseEntity
from federation.types import UserType, ReceiverVariant

logger = logging.getLogger("federation")


MAPPINGS = {
    "Accept": ActivitypubAccept,
    "Announce": ActivitypubShare,
    "Application": ActivitypubProfile,
    "Article": ActivitypubPost,
    "Delete": ActivitypubRetraction,
    "Follow": ActivitypubFollow,  # Technically not correct, but for now we support only following profiles
    "Group": ActivitypubProfile,
    "Note": ActivitypubPost,
    "Organization": ActivitypubProfile,
    "Page": ActivitypubPost,
    "Person": ActivitypubProfile,
    "Service": ActivitypubProfile,
}

OBJECTS = (
    "Application",
    "Article",
    "Group",
    "Note",
    "Organization",
    "Page",
    "Person",
    "Service",
)

UNDO_MAPPINGS = {
    "Follow": ActivitypubFollow,
    "Announce": ActivitypubRetraction,
}


def element_to_objects(payload: Dict) -> List:
    """
    Transform an Element to a list of entities.
    """
    cls = None
    entities = []
    is_object = True if payload.get('type') in OBJECTS else False
    if payload.get('type') == "Delete":
        cls = ActivitypubRetraction
    elif payload.get('type') == "Undo":
        if isinstance(payload.get('object'), dict):
            cls = UNDO_MAPPINGS.get(payload["object"]["type"])
    elif isinstance(payload.get('object'), dict) and payload["object"].get('type'):
        if payload["object"]["type"] == "Note" and payload["object"].get("inReplyTo"):
            cls = ActivitypubComment
        else:
            cls = MAPPINGS.get(payload["object"]["type"])
    else:
        cls = MAPPINGS.get(payload.get('type'))
    if not cls:
        return []

    transformed = transform_attributes(payload, cls, is_object=is_object)
    entity = cls(**transformed)
    # Add protocol name
    entity._source_protocol = "activitypub"
    # Save element object to entity for possible later use
    entity._source_object = payload
    # Extract receivers
    entity._receivers = extract_receivers(payload)
    # Extract children
    if payload.get("object") and isinstance(payload.get("object"), dict):
        # Try object if exists
        entity._children = extract_attachments(payload.get("object"))
    else:
        # Try payload itself
        entity._children = extract_attachments(payload)

    if hasattr(entity, "post_receive"):
        entity.post_receive()

    try:
        entity.validate()
    except ValueError as ex:
        logger.error("Failed to validate entity %s: %s", entity, ex, extra={
            "transformed": transformed,
        })
        return []
    # Extract mentions
    entity._mentions = entity.extract_mentions()

    entities.append(entity)

    return entities


def extract_attachments(payload: Dict) -> List[Image]:
    """
    Extract images from attachments.

    There could be other attachments, but currently we only extract images.
    """
    attachments = []
    for item in payload.get('attachment', []):
        if item.get("type") == "Document" and item.get("mediaType") in IMAGE_TYPES:
            if item.get('pyfed:inlineImage', False):
                # Skip this image as it's indicated to be inline in content and source already
                continue
            attachments.append(
                Image(
                    url=item.get('url'),
                    name=item.get('name') or "",
                )
            )
    return attachments


def extract_receiver(payload: Dict, receiver: str) -> Optional[UserType]:
    """
    Transform a single receiver ID to a UserType.
    """
    actor = payload.get("actor") or payload.get("attributedTo") or ""
    if receiver == NAMESPACE_PUBLIC:
        # Ignore since we already store "public" as a boolean on the entity
        return
    # Check for this being a list reference to followers of an actor?
    # TODO: terrible hack! the way some platforms deliver to sharedInbox using just
    #   the followers collection as a target is annoying to us since we would have to
    #   store the followers collection references on application side, which we don't
    #   want to do since it would make application development another step more complex.
    #   So for now we're going to do a terrible assumption that
    #     1) if "followers" in ID and
    #     2) if ID starts with actor ID
    #     then; assume this is the followers collection of said actor ID.
    #   When we have a caching system, just fetch each receiver and check what it is.
    #   Without caching this would be too expensive to do.
    elif receiver.find("followers") > -1 and receiver.startswith(actor):
        return UserType(id=actor, receiver_variant=ReceiverVariant.FOLLOWERS)
    # Assume actor ID
    return UserType(id=receiver, receiver_variant=ReceiverVariant.ACTOR)


def extract_receivers(payload: Dict) -> List[UserType]:
    """
    Exctract receivers from a payload.
    """
    receivers = []
    for key in ("to", "cc"):
        receiver = payload.get(key)
        if isinstance(receiver, list):
            for item in receiver:
                extracted = extract_receiver(payload, item)
                if extracted:
                    receivers.append(extracted)
        elif isinstance(receiver, str):
            extracted = extract_receiver(payload, receiver)
            if extracted:
                receivers.append(extracted)
    return receivers


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
        ActivitypubAccept, ActivitypubFollow, ActivitypubProfile, ActivitypubPost, ActivitypubComment,
        ActivitypubRetraction, ActivitypubShare,
    ]:
        # Already fine
        outbound = entity
    elif cls == Accept:
        outbound = ActivitypubAccept.from_base(entity)
    elif cls == Follow:
        outbound = ActivitypubFollow.from_base(entity)
    elif cls == Post:
        outbound = ActivitypubPost.from_base(entity)
    elif cls == Profile:
        outbound = ActivitypubProfile.from_base(entity)
    elif cls == Retraction:
        outbound = ActivitypubRetraction.from_base(entity)
    elif cls == Comment:
        outbound = ActivitypubComment.from_base(entity)
    elif cls == Share:
        outbound = ActivitypubShare.from_base(entity)
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
    return outbound


def message_to_objects(
        message: Dict, sender: str, sender_key_fetcher: Callable[[str], str] = None, user: UserType = None,
) -> List:
    """
    Takes in a message extracted by a protocol and maps it to entities.
    """
    # We only really expect one element here for ActivityPub.
    return element_to_objects(message)


def transform_attribute(
        key: str, value: Union[str, Dict, int], transformed: Dict, cls, is_object: bool, payload: Dict,
) -> None:
    if value is None:
        value = ""
    if key == "id":
        if is_object:
            if cls == ActivitypubRetraction:
                transformed["target_id"] = value
                transformed["entity_type"] = "Object"
            else:
                transformed["id"] = value
        elif cls in (ActivitypubProfile, ActivitypubShare):
            transformed["id"] = value
        else:
            transformed["activity_id"] = value
    elif key == "actor":
        transformed["actor_id"] = value
    elif key == "attributedTo" and is_object:
        transformed["actor_id"] = value
    elif key in ("content", "source"):
        if payload.get('source') and isinstance(payload.get("source"), dict):
            if payload.get('source').get('mediaType') == "text/html":
                transformed["_rendered_content"] = payload.get('content')
                transformed["_media_type"] = "text/html"
                transformed["raw_content"] = markdownify(payload.get('source').get('content')).strip()
            else:
                transformed["_media_type"] = payload.get('source').get('mediaType')
                transformed["_rendered_content"] = payload.get("content").strip()
                transformed["raw_content"] = payload.get('source').get('content').strip()
        else:
            transformed["raw_content"] = markdownify(value).strip()
            # Assume HTML by convention
            transformed["_rendered_content"] = value.strip()
            transformed["_media_type"] = "text/html"
    elif key == "inboxes" and isinstance(value, dict):
        if "inboxes" not in transformed:
            transformed["inboxes"] = {"private": None, "public": None}
        if value.get('sharedInbox'):
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
        if not transformed["inboxes"]["public"]:
            transformed["inboxes"]["public"] = value
    elif key == "inReplyTo":
        transformed["target_id"] = value
    elif key == "name":
        transformed["name"] = value or ""
    elif key == "object" and not is_object:
        if isinstance(value, dict):
            if cls == ActivitypubAccept:
                transformed["target_id"] = value.get("id")
            elif cls == ActivitypubFollow:
                transformed["target_id"] = value.get("object")
            else:
                transform_attributes(value, cls, transformed, is_object=True)
        else:
            transformed["target_id"] = value
    elif key == "preferredUsername":
        transformed["username"] = value
    elif key == "publicKey":
        transformed["public_key"] = value.get('publicKeyPem', '')
    elif key == "summary" and cls == ActivitypubProfile:
        transformed["raw_content"] = value
    elif key in ("to", "cc"):
        if isinstance(value, list) and NAMESPACE_PUBLIC in value:
            transformed["public"] = True
        elif value == NAMESPACE_PUBLIC:
            transformed["public"] = True
    elif key == "type":
        if value == "Undo":
            transformed["following"] = False
    elif key == "url":
        transformed["url"] = value


def transform_attributes(payload: Dict, cls, transformed: Dict = None, is_object: bool = False) -> Dict:
    if not transformed:
        transformed = {}
    for key, value in payload.items():
        transform_attribute(key, value, transformed, cls, is_object, payload)
    return transformed
