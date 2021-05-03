import json
import logging
import mimetypes
import os
from typing import Dict, List, Optional
from urllib.parse import quote
from uuid import uuid4

import requests
# noinspection PyPackageRequirements
from slugify import slugify

from federation.entities.base import Post, Profile
from federation.entities.matrix.enums import EventType
from federation.entities.mixins import BaseEntity
from federation.entities.utils import get_base_attributes, get_profile
from federation.utils.django import get_configuration
from federation.utils.matrix import get_matrix_configuration, appservice_auth_header
from federation.utils.network import fetch_document, fetch_file

logger = logging.getLogger("federation")


class MatrixEntityMixin(BaseEntity):
    _event_type: str = None
    _payloads: List[Dict] = []
    _profile_room_id = None
    _txn_id: str = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # We always require an mxid
        self._required.append('mxid')
        # Create a transaction ID
        self._txn_id = str(uuid4())

    @property
    def event_type(self) -> str:
        return self._event_type

    @classmethod
    def from_base(cls, entity):
        # type: (BaseEntity) -> MatrixEntityMixin
        # noinspection PyArgumentList
        return cls(**get_base_attributes(entity))

    # noinspection PyMethodMayBeStatic
    def get_endpoint(self) -> str:
        config = get_matrix_configuration()
        return f"{config['homeserver_base_url']}/_matrix/client/r0"

    # noinspection PyMethodMayBeStatic
    def get_endpoint_media(self) -> str:
        config = get_matrix_configuration()
        return f"{config['homeserver_base_url']}/_matrix/media/r0"

    def get_profile_room_id(self):
        # TODO: we should cache these.
        doc, status, error = fetch_document(
            url=f"{self.get_endpoint()}/directory/room/{self.profile_room_alias_url_safe}",
            extra_headers=appservice_auth_header(),
        )
        if status == 200:
            data = json.loads(doc)
            self._profile_room_id = data["room_id"]

    # noinspection PyMethodMayBeStatic
    def payloads(self) -> List[Dict]:
        return self._payloads

    @property
    def profile_room_alias(self):
        return f"#{self.mxid}"

    @property
    def profile_room_alias_url_safe(self):
        return f"{quote(self.profile_room_alias)}"

    @property
    def server_name(self) -> str:
        config = get_matrix_configuration()
        return config['homeserver_name']

    @property
    def txn_id(self) -> str:
        return self._txn_id


class MatrixRoomMessage(Post, MatrixEntityMixin):
    _event_type = EventType.ROOM_MESSAGE.value
    _thread_room_event_id: str = None
    _thread_room_id: str = None

    def add_tag_room_payloads(self, tag_room_id: str):
        self._payloads.append({
            "endpoint": f"{super().get_endpoint()}/rooms/{tag_room_id}/join?user_id={self.mxid}",
            "payload": {},
        })
        self._payloads.append({
            # TODO at some point we'll need to track the event_id's, for now just random
            # When we start listening to events from the other side, we'll need to filter
            # the ones we sent. Additionally if there is going to be some kind of symlink MSC,
            # we're going to want to stop carbon copying to many rooms.
            "endpoint": f"{super().get_endpoint()}/rooms/{tag_room_id}/send/{self.event_type}/"
                        f"{str(uuid4())}?user_id={self.mxid}",
            "payload": {
                "body": self.raw_content,
                "msgtype": "m.text",
                "format": "org.matrix.custom.html",
                "formatted_body": self.rendered_content,
            },
            "method": "put",
        })

    def create_tag_room(self, tag: str) -> str:
        headers = appservice_auth_header()
        config = get_configuration()
        topic = f"Content for the tag #{tag}."
        if config.get("tags_path"):
            topic += f" Mirrored from {config['base_url']}{config['tags_path'].replace(':tag:', slugify(tag))}"
        matrix_config = get_matrix_configuration()
        response = requests.post(
            url=f"{super().get_endpoint()}/createRoom",
            json={
                "preset": "public_chat",
                "name": f"#{tag} ({matrix_config['appservice']['shortcode']} | {matrix_config['homeserver_name']})",
                "room_alias_name": self.get_tag_room_alias(tag).strip('#'),
                "topic": topic,
            },
            headers=headers,
        )
        response.raise_for_status()
        room_id = response.json()["room_id"]
        self._payloads.append({
            "endpoint": f"{super().get_endpoint()}/directory/list/room/{room_id}",
            "payload": {
                "visibility": "public",
            },
            "method": "put",
        })
        return room_id

    def create_thread_room(self):
        headers = appservice_auth_header()
        # Create the thread room
        response = requests.post(
            url=f"{super().get_endpoint()}/createRoom?user_id={self.mxid}",
            json={
                # TODO auto-invite other recipients if private chat
                "preset": "public_chat" if self.public else "private_chat",
                "name": f"Thread by {self.mxid}",
                "topic": self.url,
            },
            headers=headers,
        )
        response.raise_for_status()
        self._thread_room_id = response.json()["room_id"]
        # Send the thread message
        response = requests.put(
            url=f"{super().get_endpoint()}/rooms/{self._thread_room_id}/send/{self.event_type}/"
                f"{str(uuid4())}?user_id={self.mxid}",
            json={
                "body": self.raw_content,
                "msgtype": "m.text",
                "format": "org.matrix.custom.html",
                "formatted_body": self.rendered_content,
            },
            headers=headers,
        )
        response.raise_for_status()
        self._thread_room_event_id = response.json()["event_id"]

    def get_profile_room_id(self):
        super().get_profile_room_id()
        if not self._profile_room_id:
            from federation.entities.matrix.mappers import get_outbound_entity
            # Need to also create the profile
            profile = get_profile(self.actor_id)
            profile_entity = get_outbound_entity(profile, None)
            payloads = profile_entity.payloads()
            if payloads:
                self._payloads.extend(payloads)

    @staticmethod
    def get_tag_room_alias(tag: str) -> str:
        config = get_matrix_configuration()
        return f"#_{config['appservice']['shortcode']}_#{slugify(tag)}"

    def get_tag_room_alias_url_safe(self, tag: str) -> str:
        return f"{quote(self.get_tag_room_alias(tag))}"

    def get_tag_room_id(self, tag: str) -> Optional[str]:
        # TODO: we should cache these.
        doc, status, error = fetch_document(
            url=f"{self.get_endpoint()}/directory/room/{self.get_tag_room_alias_url_safe(tag)}",
            extra_headers=appservice_auth_header(),
        )
        if status == 200:
            data = json.loads(doc)
            return data["room_id"]

    def payloads(self) -> List[Dict]:
        payloads = super().payloads()
        payloads.append({
            "endpoint": f"{super().get_endpoint()}/rooms/{self._profile_room_id}/send/{self.event_type}/"
                        f"{self.txn_id}?user_id={self.mxid}",
            "payload": {
                "body": self.raw_content,
                "msgtype": "m.text",
                "format": "org.matrix.custom.html",
                "formatted_body": self.rendered_content,
                # Fields to emulate Cerulean
                "org.matrix.cerulean.event_id": self._thread_room_event_id,
                "org.matrix.cerulean.room_id": self._thread_room_id,
                "org.matrix.cerulean.root": True,
            },
            "method": "put",
        })
        # Tag the thread room as low priority
        payloads.append({
            "endpoint": f"{super().get_endpoint()}/user/{self.mxid}/rooms/{self._thread_room_id}/tags/m.lowpriority"
                        f"?user_id={self.mxid}",
            "payload": {
                "order": 0,
            },
            "method": "put",
        })
        return payloads

    def pre_send(self):
        """
        Do various pre-send things.
        """
        super().pre_send()
        # Get profile room ID
        self.get_profile_room_id()
        # Upload embedded images and replace the HTTP urls in the message with MXC urls so clients show the images
        self.upload_embedded_images()
        # Create thread room
        self.create_thread_room()
        # Process tags if public post
        if self.public:
            for tag in self.tags:
                tag_room_id = self.get_tag_room_id(tag)
                if not tag_room_id:
                    # noinspection PyBroadException
                    try:
                        tag_room_id = self.create_tag_room(tag)
                    except Exception as ex:
                        logger.warning("Failed to create tag room for tag %s for post %s: %s", tag, self.id, ex)
                        continue
                self.add_tag_room_payloads(tag_room_id)

    def upload_embedded_images(self):
        """
        Upload embedded images

        Replaces the HTTP urls in the message with MXC urls so that Matrix clients will show the images.
        """
        for image in self.embedded_images:
            url, name = image
            headers = appservice_auth_header()
            content_type, _encoding = mimetypes.guess_type(url)
            headers["Content-Type"] = content_type
            # Random name if none
            if not name:
                name = f"{uuid4()}{mimetypes.guess_extension(content_type, strict=False)}"
            # Need to fetch it locally first
            # noinspection PyBroadException
            try:
                image_file = fetch_file(url=url, timeout=60)
            except Exception as ex:
                logger.warning("MatrixRoomMessage.pre_send | Failed to retrieve image %s to be uploaded: %s",
                               url, ex)
                continue
            # Then upload
            headers["Content-Length"] = str(os.stat(image_file).st_size)
            # noinspection PyBroadException
            try:
                with open(image_file, "rb") as f:
                    response = requests.post(
                        f"{super().get_endpoint_media()}/upload?filename={quote(name)}&user_id={self.mxid}",
                        data=f.read(),
                        headers=headers,
                        timeout=60,
                    )
                response.raise_for_status()
            except Exception as ex:
                logger.warning("MatrixRoomMessage.pre_send | Failed to upload image %s: %s",
                               url, ex)
                continue
            finally:
                os.unlink(image_file)
            # Replace in raw content
            try:
                logger.debug("MatrixRoomMessage.pre_send | Got response %s", response.json())
                content_uri = response.json()["content_uri"]
                self.raw_content = self.raw_content.replace(url, content_uri)
            except Exception as ex:
                logger.error("MatrixRoomMessage.pre_send | Failed to find content_uri from the image upload "
                             "response: %s", ex)


class MatrixProfile(Profile, MatrixEntityMixin):
    _remote_profile_create_needed = False
    _remote_room_create_needed = False

    def create_profile_room(self):
        headers = appservice_auth_header()
        response = requests.post(
            url=f"{super().get_endpoint()}/createRoom?user_id={self.mxid}",
            json={
                "name": self.name,
                "preset": "public_chat" if self.public else "private_chat",
                "room_alias_name": f"@{self.localpart}",
                "topic": f"Profile room of {self.url}",
            },
            headers=headers,
        )
        response.raise_for_status()
        self._profile_room_id = response.json()["room_id"]

    def register_user(self):
        headers = appservice_auth_header()
        response = requests.post(
            url=f"{super().get_endpoint()}/register",
            json={
                "username": f"{self.localpart}",
                "type": "m.login.application_service",
            },
            headers=headers,
        )
        response.raise_for_status()

    @property
    def localpart(self) -> str:
        return self.mxid.replace("@", "").replace(f":{self.server_name}", "")

    def payloads(self) -> List[Dict]:
        payloads = super().payloads()
        if self._remote_profile_create_needed:
            self.register_user()
        if self._remote_room_create_needed:
            self.create_profile_room()
        payloads.append({
            "endpoint": f"{super().get_endpoint()}/profile/{self.mxid}/displayname?user_id={self.mxid}",
            "payload": {
                "displayname": self.name,
            },
            "method": "put",
        })
        # TODO avatar url in mxc format
        return payloads

    def pre_send(self):
        """
        Check whether we need to create the user or their profile room.
        """
        doc, status, error = fetch_document(
            url=f"{super().get_endpoint()}/profile/{self.mxid}",
            extra_headers=appservice_auth_header(),
        )
        if status != 200:
            self._remote_profile_create_needed = True
        else:
            self.get_profile_room_id()

        if self._remote_profile_create_needed or not self._profile_room_id:
            self._remote_room_create_needed = True
