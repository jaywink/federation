# -*- coding: utf-8 -*-
import logging
from datetime import datetime

from lxml import etree

from federation.entities.base import Image, Relationship, Post, Reaction, Comment, Profile
from federation.entities.diaspora.entities import (
    DiasporaPost, DiasporaComment, DiasporaLike, DiasporaRequest, DiasporaProfile)


logger = logging.getLogger("social-federation")

MAPPINGS = {
    "status_message": DiasporaPost,
    "photo": Image,
    "comment": DiasporaComment,
    "like": DiasporaLike,
    "request": DiasporaRequest,
    "profile": DiasporaProfile,
}

BOOLEAN_KEYS = [
    "public",
    "nsfw",
]

DATETIME_KEYS = [
    "created_at",
]


def xml_children_as_dict(node):
    """Turn the children of node <xml> into a dict, keyed by tag name.

    This is only a shallow conversation - child nodes are not recursively processed.
    """
    return dict((e.tag, e.text) for e in node)


def message_to_objects(message):
    """Takes in a message extracted by a protocol and maps it to entities."""
    doc = etree.fromstring(message)
    entities = []
    for element in doc.iter():
        cls = MAPPINGS.get(element.tag, None)
        if cls:
            attrs = xml_children_as_dict(element)
            transformed = transform_attributes(attrs)
            if hasattr(cls, "fill_extra_attributes"):
                transformed = cls.fill_extra_attributes(transformed)
            entity = cls(**transformed)
            try:
                entity.validate()
                entities.append(entity)
            except ValueError as ex:
                logger.error("Failed to validate entity %s: %s", entity, ex, extra={
                    "attrs": attrs,
                    "transformed": transformed,
                })
                continue
            if cls == DiasporaRequest:
                # We support sharing/following separately, so also generate base Relationship for the following part
                transformed.update({"relationship": "following"})
                entity = Relationship(**transformed)
                entities.append(entity)
    return entities


def transform_attributes(attrs):
    """Transform some attribute keys."""
    transformed = {}
    for key, value in attrs.items():
        if key in ["raw_message", "text"]:
            transformed["raw_content"] = value
        elif key in ["diaspora_handle", "sender_handle"]:
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
        elif key in BOOLEAN_KEYS:
            transformed[key] = True if value == "true" else False
        elif key in DATETIME_KEYS:
            transformed[key] = datetime.strptime(value, "%Y-%m-%d %H:%M:%S %Z")
        else:
            transformed[key] = value or ""
    return transformed


def get_outbound_entity(entity):
    """Get the correct outbound entity for this protocol.

    We might have to look at entity values to decide the correct outbound entity.
    If we cannot find one, we should raise as conversion cannot be guaranteed to the given protocol.

    Args:
        entity - any of the base entity types from federation.entities.base

    Returns:
        An instance of the correct protocol specific entity.
    """
    cls = entity.__class__
    if cls in [DiasporaPost, DiasporaRequest, DiasporaComment, DiasporaLike, DiasporaProfile]:
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
    raise ValueError("Don't know how to convert this base entity to Diaspora protocol entities.")
