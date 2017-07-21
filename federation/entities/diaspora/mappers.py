import logging
from datetime import datetime

from lxml import etree

from federation.entities.base import Image, Relationship, Post, Reaction, Comment, Profile, Retraction, Follow
from federation.entities.diaspora.entities import (
    DiasporaPost, DiasporaComment, DiasporaLike, DiasporaRequest, DiasporaProfile, DiasporaRetraction,
    DiasporaRelayableMixin, DiasporaContact)
from federation.protocols.diaspora.signatures import get_element_child_info
from federation.utils.diaspora import retrieve_and_parse_profile

logger = logging.getLogger("federation")

MAPPINGS = {
    "status_message": DiasporaPost,
    "photo": Image,
    "comment": DiasporaComment,
    "like": DiasporaLike,
    "request": DiasporaRequest,
    "profile": DiasporaProfile,
    "retraction": DiasporaRetraction,
    "contact": DiasporaContact,
}

TAGS = [
    # Order is important. Any top level tags should be before possibly child tags
    "status_message", "comment", "like", "request", "profile", "retraction", "photo", "contact",
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


def element_to_objects(element, sender_key_fetcher=None, user=None):
    """Transform an Element to a list of entities recursively.

    Possible child entities are added to each entity `_children` list.

    :param tree: Element
    :param sender_key_fetcher: Function to fetch sender public key. If not given, key will always be fetched
        over network. The function should take sender handle as the only parameter.
    :param user: Optional receiving user object. If given, should have a `handle`.
    :returns: list of entities
    """
    entities = []
    cls = MAPPINGS.get(element.tag, None)
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
    # Save receiving guid to object
    if user and hasattr(user, "guid"):
        entity._receiving_guid = user.guid
    # If relayable, fetch sender key for validation
    if issubclass(cls, DiasporaRelayableMixin):
        entity._xml_tags = get_element_child_info(element, "tag")
        if sender_key_fetcher:
            entity._sender_key = sender_key_fetcher(entity.handle)
        else:
            profile = retrieve_and_parse_profile(entity.handle)
            if profile:
                entity._sender_key = profile.public_key
    try:
        entity.validate()
    except ValueError as ex:
        logger.error("Failed to validate entity %s: %s", entity, ex, extra={
            "attrs": attrs,
            "transformed": transformed,
        })
        return []
    # Do child elements
    for child in element:
        entity._children.extend(element_to_objects(child))
    # Add to entities list
    entities.append(entity)
    if cls == DiasporaRequest:
        # We support sharing/following separately, so also generate base Relationship for the following part
        transformed.update({"relationship": "following"})
        relationship = Relationship(**transformed)
        entities.append(relationship)
    return entities


def message_to_objects(message, sender_key_fetcher=None, user=None):
    """Takes in a message extracted by a protocol and maps it to entities.

    :param message: XML payload
    :type message: str
    :param sender_key_fetcher: Function to fetch sender public key. If not given, key will always be fetched
        over network. The function should take sender handle as the only parameter.
    :param user: Optional receiving user object. If given, should have a `handle`.
    :returns: list of entities
    """
    doc = etree.fromstring(message)
    # Future Diaspora protocol version contains the element at top level
    if doc.tag in TAGS:
        return element_to_objects(doc, sender_key_fetcher, user)
    # Legacy Diaspora protocol wraps the element in <XML><post></post></XML>, so find the right element
    for tag in TAGS:
        element = doc.find(".//%s" % tag)
        if element is not None:
            return element_to_objects(element, sender_key_fetcher, user)
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
        if key in ["raw_message", "text"]:
            transformed["raw_content"] = value
        elif key in ["diaspora_handle", "sender_handle", "author"]:
            transformed["handle"] = value
        elif key in ["recipient_handle", "recipient"]:
            transformed["target_handle"] = value
        elif key == "parent_guid":
            transformed["target_guid"] = value
        elif key == "first_name":
            transformed["name"] = value
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
        elif key in ["target_type", "type"] and cls == DiasporaRetraction:
            transformed["entity_type"] = DiasporaRetraction.entity_type_from_remote(value)
        elif key == "remote_photo_path":
            transformed["remote_path"] = value
        elif key == "remote_photo_name":
            transformed["remote_name"] = value
        elif key == "status_message_guid":
            transformed["linked_guid"] = value
            transformed["linked_type"] = "Post"
        elif key == "author_signature":
            transformed["signature"] = value
        elif key == "post_guid":
            transformed["target_guid"] = value
        elif key in BOOLEAN_KEYS:
            transformed[key] = True if value == "true" else False
        elif key in DATETIME_KEYS:
            try:
                # New style timestamps since in protocol 0.1.6
                transformed[key] = datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
            except ValueError:
                # Legacy style timestamps
                transformed[key] = datetime.strptime(value, "%Y-%m-%d %H:%M:%S %Z")
        elif key in INTEGER_KEYS:
            transformed[key] = int(value)
        else:
            transformed[key] = value or ""
    return transformed


def get_outbound_entity(entity, private_key):
    """Get the correct outbound entity for this protocol.

    We might have to look at entity values to decide the correct outbound entity.
    If we cannot find one, we should raise as conversion cannot be guaranteed to the given protocol.

    Private key of author is needed to be passed for signing the outbound entity.

    :arg entity: An entity instance which can be of a base or protocol entity class.
    :returns: Protocol specific entity class instance.
    :raises ValueError: If conversion cannot be done.
    """
    if getattr(entity, "outbound_doc", None):
        # If the entity already has an outbound doc, just return the entity as is
        return entity
    outbound = None
    cls = entity.__class__
    if cls in [DiasporaPost, DiasporaRequest, DiasporaComment, DiasporaLike, DiasporaProfile, DiasporaRetraction,
               DiasporaContact]:
        # Already fine
        outbound = entity
    elif cls == Post:
        outbound = DiasporaPost.from_base(entity)
    elif cls == Comment:
        outbound = DiasporaComment.from_base(entity)
    elif cls == Reaction:
        if entity.reaction == "like":
            outbound = DiasporaLike.from_base(entity)
    elif cls == Relationship:
        if entity.relationship in ["sharing", "following"]:
            # Unfortunately we must send out in both cases since in Diaspora they are the same thing
            outbound = DiasporaRequest.from_base(entity)
    elif cls == Follow:
        outbound = DiasporaContact.from_base(entity)
    elif cls == Profile:
        outbound = DiasporaProfile.from_base(entity)
    elif cls == Retraction:
        outbound = DiasporaRetraction.from_base(entity)
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
