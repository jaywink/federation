# -*- coding: utf-8 -*-
import logging
from datetime import datetime

from lxml import etree

from federation.entities.base import Image, Relationship, Post, Reaction, Comment, Profile, Retraction, SignedMixin
from federation.entities.diaspora.entities import (
    DiasporaPost, DiasporaComment, DiasporaLike, DiasporaRequest, DiasporaProfile, DiasporaRetraction)
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
}

BOOLEAN_KEYS = [
    "public",
    "nsfw",
]

DATETIME_KEYS = [
    "created_at",
]

INTEGER_KEYS = [
    "height",
    "width",
]

def xml_children_as_dict(node):
    """Turn the children of node <xml> into a dict, keyed by tag name.

    This is only a shallow conversation - child nodes are not recursively processed.
    """
    return dict((e.tag, e.text) for e in node)


def element_to_objects(tree, sender_key_fetcher=None):
    """Transform an Element tree to a list of entities recursively.

    Possible child entities are added to each entity `_children` list.

    :param tree: Element
    :returns: list of entities
    """
    entities = []
    for element in tree:
        cls = MAPPINGS.get(element.tag, None)
        if not cls:
            continue

        attrs = xml_children_as_dict(element)
        transformed = transform_attributes(attrs)
        if hasattr(cls, "fill_extra_attributes"):
            transformed = cls.fill_extra_attributes(transformed)
        entity = cls(**transformed)
        # Add protocol name
        entity._source_protocol = "diaspora"
        # Save element object to entity for possible later use
        entity._source_object = element
        # If signable, fetch sender key
        if issubclass(cls, SignedMixin):
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
            continue
        # Do child elements
        entity._children = element_to_objects(element)
        # Add to entities list
        entities.append(entity)
        if cls == DiasporaRequest:
            # We support sharing/following separately, so also generate base Relationship for the following part
            transformed.update({"relationship": "following"})
            relationship = Relationship(**transformed)
            entities.append(relationship)
    return entities


def message_to_objects(message, sender_key_fetcher=None):
    """Takes in a message extracted by a protocol and maps it to entities.

    :param message: XML payload
    :type message: str
    :param sender_key_fetcher: Function to fetch sender public key. If not given, key will always be fetched
        over network
    :returns: list of entities
    """
    doc = etree.fromstring(message)
    if doc[0].tag == "post":
        # Skip the top <post> element if it exists
        doc = doc[0]
    entities = element_to_objects(doc, sender_key_fetcher)
    return entities


def transform_attributes(attrs):
    """Transform some attribute keys."""
    transformed = {}
    for key, value in attrs.items():
        if key in ["raw_message", "text"]:
            transformed["raw_content"] = value
        elif key in ["diaspora_handle", "sender_handle", "author"]:
            transformed["handle"] = value
        elif key == "recipient_handle":
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
            transformed["tag_list"] = value.replace("#", "").split(" ")
        elif key == "bio":
            transformed["raw_content"] = value
        elif key == "searchable":
            transformed["public"] = True if value == "true" else False
        elif key == "target_type":
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


def get_outbound_entity(entity):
    """Get the correct outbound entity for this protocol.

    We might have to look at entity values to decide the correct outbound entity.
    If we cannot find one, we should raise as conversion cannot be guaranteed to the given protocol.

    :arg entity: An entity instance which can be of a base or protocol entity class.
    :returns: Protocol specific entity class instance.
    :raises ValueError: If conversion cannot be done.
    """
    cls = entity.__class__
    if cls in [DiasporaPost, DiasporaRequest, DiasporaComment, DiasporaLike, DiasporaProfile, DiasporaRetraction]:
        # Already fine
        return entity
    elif cls == Post:
        return DiasporaPost.from_base(entity)
    elif cls == Comment:
        return DiasporaComment.from_base(entity)
    elif cls == Reaction:
        if entity.reaction == "like":
            return DiasporaLike.from_base(entity)
    elif cls == Relationship:
        if entity.relationship in ["sharing", "following"]:
            # Unfortunately we must send out in both cases since in Diaspora they are the same thing
            return DiasporaRequest.from_base(entity)
    elif cls == Profile:
        return DiasporaProfile.from_base(entity)
    elif cls == Retraction:
        return DiasporaRetraction.from_base(entity)
    raise ValueError("Don't know how to convert this base entity to Diaspora protocol entities.")
