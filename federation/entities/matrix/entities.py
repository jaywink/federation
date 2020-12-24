import logging

from federation.entities.base import Post, Profile
from federation.entities.matrix.enums import EventType
from federation.entities.mixins import BaseEntity
from federation.entities.utils import get_base_attributes

logger = logging.getLogger("federation")


class MatrixEntityMixin(BaseEntity):
    _event_type: str = None
    _txn_id: str = None

    @property
    def event_type(self) -> str:
        return self._event_type

    @classmethod
    def from_base(cls, entity):
        # type: (BaseEntity) -> MatrixEntityMixin
        # noinspection PyArgumentList
        return cls(**get_base_attributes(entity))

    def get_endpoint(self, *args, **kwargs) -> str:
        return "/_matrix/client/r0/"

    @property
    def txn_id(self) -> str:
        return self._txn_id


class MatrixRoomMessage(Post, MatrixEntityMixin):
    _event_type = EventType.ROOM_MESSAGE.value

    def get_endpoint(self, fid: str, user_id: str) -> str:
        endpoint = super().get_endpoint()
        return f"{endpoint}rooms/{fid}/send/{self.event_type}/{self.txn_id}?user_id={user_id}"


class MatrixProfile(Profile, MatrixEntityMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # We always require an mxid
        self._required.add('mxid')
