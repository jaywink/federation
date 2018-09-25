from enum import Enum


class ActivityType(Enum):
    CREATE = "Create"
    DELETE = "Delete"
    UPDATE = "Update"


class ActorType(Enum):
    NOTE = "Note"
    PERSON = "Person"
