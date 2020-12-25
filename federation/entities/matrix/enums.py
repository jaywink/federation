from enum import Enum


class EnumBase(Enum):
    @classmethod
    def values(cls):
        return [value.value for value in cls.__members__.values()]


class EventType(EnumBase):
    ROOM_MESSAGE = "m.room.message"
