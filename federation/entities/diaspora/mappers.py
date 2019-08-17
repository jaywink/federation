import logging
from datetime import datetime
from typing import Callable, List

# noinspection PyPackageRequirements
from Crypto.PublicKey.RSA import RsaKey
from lxml import etree

from federation.entities.base import Comment, Follow, Post, Profile, Reaction, Retraction, Share
from federation.entities.diaspora.entities import (
    DiasporaComment, DiasporaContact, DiasporaLike, DiasporaPost,
    DiasporaProfile, DiasporaReshare, DiasporaRetraction,
    DiasporaImage)
from federation.entities.diaspora.mixins import DiasporaRelayableMixin
from federation.entities.mixins import BaseEntity
from federation.protocols.diaspora.signatures import get_element_child_info
from federation.types import UserType, ReceiverVariant
from federation.utils.diaspora import retrieve_and_parse_profile

logger = logging.getLogger("federation")

MAPPINGS = {
    "status_message": DiasporaPost,
    "comment": DiasporaComment,
    "photo": DiasporaImage,
    "like": DiasporaLike,
    "profile": DiasporaProfile,
    "retraction": DiasporaRetraction,
    "contact": DiasporaContact,
    "reshare": DiasporaReshare,
}

TAGS = [
    # Order is important. Any top level tags should be before possibly child tags
    "reshare", "status_message", "comment", "like", "request", "profile", "retraction", "photo", "contact",
]

BOOLEAN_KEYS = (
    "public",
    "nsfw",
    "following",
    "sharing",
)

DATETIME_KEYS = (
    "created_at",
)

INTEGER_KEYS = (
    "height",
    "width",
)


def xml_children_as_dict(node):
    """Turn the children of node <xml> into a dict, keyed by tag name.

    This is only a shallow conversation - child nodes are not recursively processed.
    """
    return dict((e.tag, e.text) for e in node)


def check_sender_and_entity_handle_match(sender_handle, entity_handle):
    """Ensure that sender and entity handles match.

    Basically we've already verified the sender is who they say when receiving the payload. However, the sender might
    be trying to set another author in the payload itself, since Diaspora has the sender in both the payload headers
    AND the object. We must ensure they're the same.
    """
    if sender_handle != entity_handle:
        logger.warning("sender_handle and entity_handle don't match, aborting! sender_handle: %s, entity_handle: %s",
                       sender_handle, entity_handle)
        return False
    return True


def element_to_objects(
        element: etree.ElementTree, sender: str, sender_key_fetcher: Callable[[str], str] = None, user: UserType = None,
) -> List:
    """Transform an Element to a list of entities recursively.

    Possible child entities are added to each entity ``_children`` list.

    Optional parameter ``sender_key_fetcher`` can be a function to fetch sender public key.
    If not given, key will always be fetched over the network. The function should take sender as the only parameter.
    """
    entities = []
    cls = MAPPINGS.get(element.tag)
    if not cls:
        return []

    attrs = xml_children_as_dict(element)
    transformed = transform_attributes(attrs, cls)
    if hasattr(cls, "fill_extra_attributes"):
        transformed = cls.fill_extra_attributes(transformed)
    entity = cls(**transformed)
    # Add protocol name
    entity._source_protocol = "diaspora"
    # Save element object to entity for possible later use
    entity._source_object = etree.tostring(element)

    # Save receivers on the entity
    if user:
        # Single receiver
        entity._receivers = [UserType(id=user.id, receiver_variant=ReceiverVariant.ACTOR)]
    else:
        # Followers
        entity._receivers = [UserType(id=sender, receiver_variant=ReceiverVariant.FOLLOWERS)]

    if issubclass(cls, DiasporaRelayableMixin):
        # If relayable, fetch sender key for validation
        entity._xml_tags = get_element_child_info(element, "tag")
        if sender_key_fetcher:
            entity._sender_key = sender_key_fetcher(entity.actor_id)
        else:
            profile = retrieve_and_parse_profile(entity.handle)
            if profile:
                entity._sender_key = profile.public_key
    else:
        # If not relayable, ensure handles match
        if not check_sender_and_entity_handle_match(sender, entity.handle):
            return []
    try:
        entity.validate()
    except ValueError as ex:
        logger.error("Failed to validate entity %s: %s", entity, ex, extra={
            "attrs": attrs,
            "transformed": transformed,
        })
        return []
    # Extract mentions
    entity._mentions = entity.extract_mentions()
    # Do child elements
    for child in element:
        # noinspection PyProtectedMember
        entity._children.extend(element_to_objects(child, sender, user=user))
    # Add to entities list
    entities.append(entity)
    return entities


def message_to_objects(
        message: str, sender: str, sender_key_fetcher:Callable[[str], str]=None, user: UserType =None,
) -> List:
    """Takes in a message extracted by a protocol and maps it to entities.

    :param message: XML payload
    :type message: str
    :param sender: Payload sender id
    :type message: str
    :param sender_key_fetcher: Function to fetch sender public key. If not given, key will always be fetched
        over network. The function should take sender handle as the only parameter.
    :param user: Optional receiving user object. If given, should have a `handle`.
    :returns: list of entities
    """
    doc = etree.fromstring(message)
    if doc.tag in TAGS:
        return element_to_objects(doc, sender, sender_key_fetcher, user)
    return []


def transform_attributes(attrs, cls):
    """Transform some attribute keys.

    :param attrs: Properties from the XML
    :type attrs: dict
    :param cls: Class of the entity
    :type cls: class
    """
    transformed = {}
    for key, value in attrs.items():
        if value is None:
            value = ""
        if key == "text":
            transformed["raw_content"] = value
        elif key == "author":
            if cls == DiasporaProfile:
                # Diaspora Profile XML message contains no GUID. We need the guid. Fetch it.
                profile = retrieve_and_parse_profile(value)
                transformed['id'] = value
                transformed["guid"] = profile.guid
            else:
                transformed["actor_id"] = value
            transformed["handle"] = value
        elif key == 'guid':
            if cls != DiasporaProfile:
                transformed["id"] = value
                transformed["guid"] = value
        elif key in ("root_author", "recipient"):
            transformed["target_id"] = value
            transformed["target_handle"] = value
        elif key in ("target_guid", "root_guid", "parent_guid"):
            transformed["target_id"] = value
            transformed["target_guid"] = value
        elif key == "thread_parent_guid":
            transformed["root_target_id"] = value
            transformed["root_target_guid"] = value
        elif key in ("first_name", "last_name"):
            values = [attrs.get('first_name'), attrs.get('last_name')]
            values = [v for v in values if v]
            transformed["name"] = " ".join(values)
        elif key == "image_url":
            if "image_urls" not in transformed:
                transformed["image_urls"] = {}
            transformed["image_urls"]["large"] = value
        elif key == "image_url_small":
            if "image_urls" not in transformed:
                transformed["image_urls"] = {}
            transformed["image_urls"]["small"] = value
        elif key == "image_url_medium":
            if "image_urls" not in transformed:
                transformed["image_urls"] = {}
            transformed["image_urls"]["medium"] = value
        elif key == "tag_string":
            if value:
                transformed["tag_list"] = value.replace("#", "").split(" ")
        elif key == "bio":
            transformed["raw_content"] = value
        elif key == "searchable":
            transformed["public"] = True if value == "true" else False
        elif key in ["target_type"] and cls == DiasporaRetraction:
            transformed["entity_type"] = DiasporaRetraction.entity_type_from_remote(value)
        elif key == "remote_photo_path":
            transformed["url"] = f"{value}{attrs.get('remote_photo_name')}"
        elif key == "author_signature":
            transformed["signature"] = value
        elif key in BOOLEAN_KEYS:
            transformed[key] = True if value == "true" else False
        elif key in DATETIME_KEYS:
            transformed[key] = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
        elif key in INTEGER_KEYS:
            transformed[key] = int(value)
        else:
            transformed[key] = value
    return transformed


def get_outbound_entity(entity: BaseEntity, private_key: RsaKey):
    """Get the correct outbound entity for this protocol.

    We might have to look at entity values to decide the correct outbound entity.
    If we cannot find one, we should raise as conversion cannot be guaranteed to the given protocol.

    Private key of author is needed to be passed for signing the outbound entity.

    :arg entity: An entity instance which can be of a base or protocol entity class.
    :arg private_key: Private key of sender as an RSA object
    :returns: Protocol specific entity class instance.
    :raises ValueError: If conversion cannot be done.
    """
    if getattr(entity, "outbound_doc", None):
        # If the entity already has an outbound doc, just return the entity as is
        return entity
    outbound = None
    cls = entity.__class__
    if cls in [DiasporaPost, DiasporaImage, DiasporaComment, DiasporaLike, DiasporaProfile, DiasporaRetraction,
               DiasporaContact, DiasporaReshare]:
        # Already fine
        outbound = entity
    elif cls == Post:
        outbound = DiasporaPost.from_base(entity)
    elif cls == Comment:
        outbound = DiasporaComment.from_base(entity)
    elif cls == Reaction:
        if entity.reaction == "like":
            outbound = DiasporaLike.from_base(entity)
    elif cls == Follow:
        outbound = DiasporaContact.from_base(entity)
    elif cls == Profile:
        outbound = DiasporaProfile.from_base(entity)
    elif cls == Retraction:
        outbound = DiasporaRetraction.from_base(entity)
    elif cls == Share:
        outbound = DiasporaReshare.from_base(entity)
    if not outbound:
        raise ValueError("Don't know how to convert this base entity to Diaspora protocol entities.")
    if isinstance(outbound, DiasporaRelayableMixin) and not outbound.signature:
        # Sign by author if not signed yet. We don't want to overwrite any existing signature in the case
        # that this is being sent by the parent author
        outbound.sign(private_key)
        # If missing, also add same signature to `parent_author_signature`. This is required at the moment
        # in all situations but is apparently being removed.
        # TODO: remove this once Diaspora removes the extra signature
        outbound.parent_signature = outbound.signature
    return outbound
