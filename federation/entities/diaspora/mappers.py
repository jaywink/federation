# -*- coding: utf-8 -*-
from datetime import datetime

from lxml import etree

from federation.entities.base import Image
from federation.entities.diaspora.entities import DiasporaPost, DiasporaComment, DiasporaLike

MAPPINGS = {
    "status_message": DiasporaPost,
    "photo": Image,
    "comment": DiasporaComment,
    "like": DiasporaLike,
}

BOOLEAN_KEYS = [
    "public",
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
            transformed = transform_attributes(cls, attrs)
            entity = cls(**transformed)
            entities.append(entity)
    return entities


def transform_attributes(cls, attrs):
    """Transform some attribute keys."""
    transformed = {}
    for key, value in attrs.items():
        if key in ["raw_message", "text"]:
            transformed["raw_content"] = value
        elif key == "diaspora_handle":
            transformed["handle"] = value
        elif key == "parent_guid":
            transformed["target_guid"] = value
        elif key in BOOLEAN_KEYS:
            transformed[key] = True if value == "true" else False
        elif key in DATETIME_KEYS:
            transformed[key] = datetime.strptime(value, "%Y-%m-%d %H:%M:%S %Z")
        else:
            transformed[key] = value
    return transformed
