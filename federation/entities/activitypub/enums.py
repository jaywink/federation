from enum import Enum


class EnumBase(Enum):
    @classmethod
    def values(cls):
        return [value.value for value in cls.__members__.values()]


class ActivityType(EnumBase):
    ACCEPT = "Accept"
    CREATE = "Create"
    DELETE = "Delete"
    FOLLOW = "Follow"
    UPDATE = "Update"


class ActorType(EnumBase):
    PERSON = "Person"


class ObjectType(EnumBase):
    NOTE = "Note"
