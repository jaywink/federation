from enum import Enum


class ActivityType(Enum):
    CREATE = "Create"
    DELETE = "Delete"
    UPDATE = "Update"


class ActorType(Enum):
    PERSON = "Person"


class ObjectType(Enum):
    NOTE = "Note"
