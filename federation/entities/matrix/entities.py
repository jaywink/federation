import logging
from typing import Dict, List

from federation.entities.base import Post, Profile
from federation.entities.matrix.enums import EventType
from federation.entities.mixins import BaseEntity
from federation.entities.utils import get_base_attributes
from federation.utils.matrix import get_matrix_configuration, appservice_auth_header
from federation.utils.network import fetch_document

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
        config = get_matrix_configuration()
        return f"{config['homeserver_base_url']}/_matrix/client/r0"

    # noinspection PyMethodMayBeStatic
    def payloads(self) -> List[Dict]:
        return []

    @property
    def txn_id(self) -> str:
        return self._txn_id


class MatrixRoomMessage(Post, MatrixEntityMixin):
    _event_type = EventType.ROOM_MESSAGE.value

    def get_endpoint(self, fid: str, user_id: str) -> str:
        endpoint = super().get_endpoint()
        return f"{endpoint}/rooms/{fid}/send/{self.event_type}/{self.txn_id}?user_id={user_id}"


class MatrixProfile(Profile, MatrixEntityMixin):
    _remote_create_needed = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # We always require an mxid
        self._required.append('mxid')

    @property
    def localpart(self) -> str:
        config = get_matrix_configuration()
        return self.mxid.replace("@", "").replace(f":{config['homeserver_name']}", "")

    def payloads(self) -> List[Dict]:
        payloads = super().payloads()
        if self._remote_create_needed:
            payloads.append({
                "endpoint": f"{super().get_endpoint()}/register",
                "payload": {
                    "username": f"{self.localpart}",
                    "type": "m.login.application_service",
                },
            })
        payloads.append({
            "endpoint": f"{super().get_endpoint()}/profile/{self.mxid}/displayname",
            "payload": {
                "displayname": self.name,
            },
            "method": "put",
        })
        # TODO avatar url in mxc format
        return payloads

    def pre_send(self):
        """
        Check whether we need to create this user.
        """
        doc, status, error = fetch_document(
            url=f"{super().get_endpoint()}/profile/{self.mxid}",
            extra_headers=appservice_auth_header(),
        )
        if status == 200:
            return

        self._remote_create_needed = True
