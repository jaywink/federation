from typing import List, Callable, Dict

from federation.entities.activitypub.entities import ActivitypubFollow, ActivitypubProfile
from federation.types import UserType

MAPPINGS = {
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
    entities.append(cls(**transformed))

    return entities


def message_to_objects(
        message: Dict, sender: str, sender_key_fetcher:Callable[[str], str]=None, user: UserType =None,
) -> List:
    """
    Takes in a message extracted by a protocol and maps it to entities.
    """
    # We only really expect one element here for ActivityPub.
    return element_to_objects(message, sender, sender_key_fetcher, user)


def transform_attribute(key, value, cls):
    if value is None:
        value = ""
    if key == "id":
        if cls == ActivitypubProfile:
            return {"id": value}
        else:
            return {"activity_id": value}
    elif key == "actor":
        return {"actor_id": value}
    elif key == "icon":
        # TODO maybe we should ditch these size constants and instead have a more flexible dict for images
        # so based on protocol there would either be one url or many by size name
        return {"image_urls": {
            "small": value,
            "medium": value,
            "large": value,
        }}
    elif key == "name":
        return {"name": value}
    elif key == "object":
        if isinstance(value, dict):
            return transform_attributes(value, cls)
        else:
            return {"target_id": value}
    elif key == "preferredUsername":
        return {"username": value}
    elif key == "publicKey":
        return {"public_key": value.get('publicKeyPem', '')}
    elif key == "url":
        return {"url": value}
    return {}


def transform_attributes(payload, cls):
    transformed = {}
    for key, value in payload.items():
        transformed.update(transform_attribute(key, value, cls))
    return transformed
