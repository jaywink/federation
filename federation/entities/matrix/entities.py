import logging

from federation.entities.base import Post, Profile
from federation.entities.mixins import BaseEntity
from federation.entities.utils import get_base_attributes

logger = logging.getLogger("federation")


class MatrixEntityMixin(BaseEntity):
    _event_type = None
    _state_key = None

    @property
    def event_type(self):
        return self._event_type

    @classmethod
    def from_base(cls, entity):
        # noinspection PyArgumentList
        return cls(**get_base_attributes(entity))

    @property
    def state_key(self):
        return self._state_key

    def to_string(self):
        # noinspection PyUnresolvedReferences
        return ""


class MatrixRoomMessage(Post, MatrixEntityMixin):
    pass


class MatrixProfile(Profile, MatrixEntityMixin):
    pass
