from enum import Enum


class EnumBase(Enum):
    @classmethod
    def values(cls):
        return [value.value for value in cls.__members__.values()]


class ActivityType(EnumBase):
    ACCEPT = "Accept"
    ANNOUNCE = "Announce"
    CREATE = "Create"
    DELETE = "Delete"
    FOLLOW = "Follow"
    UNDO = "Undo"
    UPDATE = "Update"


class ActorType(EnumBase):
    PERSON = "Person"


class ObjectType(EnumBase):
    IMAGE = "Image"
    NOTE = "Note"
    TOMBSTONE = "Tombstone"
