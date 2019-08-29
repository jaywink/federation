import json
import logging
from base64 import urlsafe_b64decode
from typing import Callable, Tuple, Union, Dict
from urllib.parse import unquote

from Crypto.PublicKey.RSA import RsaKey
from lxml import etree

from federation.entities.mixins import BaseEntity
from federation.exceptions import EncryptedMessageError, NoSenderKeyFoundError
from federation.protocols.diaspora.encrypted import EncryptedPayload
from federation.protocols.diaspora.magic_envelope import MagicEnvelope
from federation.types import UserType, RequestType
from federation.utils.diaspora import fetch_public_key
from federation.utils.text import decode_if_bytes, encode_if_text, validate_handle

logger = logging.getLogger("federation")

PROTOCOL_NAME = "diaspora"
PROTOCOL_NS = "https://joindiaspora.com/protocol"
MAGIC_ENV_TAG = "{http://salmon-protocol.org/ns/magic-env}env"


def identify_id(id: str) -> bool:
    """
    Try to identify if this ID is a Diaspora ID.
    """
    return validate_handle(id)


# noinspection PyBroadException
def identify_request(request: RequestType):
    """Try to identify whether this is a Diaspora request.

    Try first public message. Then private message. The check if this is a legacy payload.
    """
    # Private encrypted JSON payload
    try:
        data = json.loads(decode_if_bytes(request.body))
        if "encrypted_magic_envelope" in data:
            return True
    except Exception:
        pass
    # Public XML payload
    try:
        xml = etree.fromstring(encode_if_text(request.body))
        if xml.tag == MAGIC_ENV_TAG:
            return True
    except Exception:
        pass
    return False


class Protocol:
    """Diaspora protocol parts

    Original legacy implementation mostly taken from Pyaspora (https://github.com/lukeross/pyaspora).
    """
    content = None
    doc = None
    get_contact_key = None
    user = None
    sender_handle = None

    def get_json_payload_magic_envelope(self, payload):
        """Encrypted JSON payload"""
        private_key = self._get_user_key()
        return EncryptedPayload.decrypt(payload=payload, private_key=private_key)

    def store_magic_envelope_doc(self, payload):
        """Get the Magic Envelope, trying JSON first."""
        try:
            json_payload = json.loads(decode_if_bytes(payload))
        except ValueError:
            # XML payload
            xml = unquote(decode_if_bytes(payload))
            xml = xml.lstrip().encode("utf-8")
            logger.debug("diaspora.protocol.store_magic_envelope_doc: xml payload: %s", xml)
            self.doc = etree.fromstring(xml)
        else:
            logger.debug("diaspora.protocol.store_magic_envelope_doc: json payload: %s", json_payload)
            self.doc = self.get_json_payload_magic_envelope(json_payload)

    def receive(
            self,
            request: RequestType,
            user: UserType = None,
            sender_key_fetcher: Callable[[str], str] = None,
            skip_author_verification: bool = False) -> Tuple[str, str]:
        """Receive a payload.

        For testing purposes, `skip_author_verification` can be passed. Authorship will not be verified."""
        self.user = user
        self.get_contact_key = sender_key_fetcher
        self.store_magic_envelope_doc(request.body)
        # Open payload and get actual message
        self.content = self.get_message_content()
        # Get sender handle
        self.sender_handle = self.get_sender()
        # Verify the message is from who it claims to be
        if not skip_author_verification:
            self.verify_signature()
        return self.sender_handle, self.content

    def _get_user_key(self):
        if not getattr(self.user, "private_key", None):
            raise EncryptedMessageError("Cannot decrypt private message without user key")
        return self.user.rsa_private_key

    def get_sender(self):
        return MagicEnvelope.get_sender(self.doc)

    def get_message_content(self):
        """
        Given the Slap XML, extract out the payload.
        """
        body = self.doc.find(
            ".//{http://salmon-protocol.org/ns/magic-env}data").text

        body = urlsafe_b64decode(body.encode("ascii"))

        logger.debug("diaspora.protocol.get_message_content: %s", body)
        return body

    def verify_signature(self):
        """
        Verify the signed XML elements to have confidence that the claimed
        author did actually generate this message.
        """
        if self.get_contact_key:
            sender_key = self.get_contact_key(self.sender_handle)
        else:
            sender_key = fetch_public_key(self.sender_handle)
        if not sender_key:
            raise NoSenderKeyFoundError("Could not find a sender contact to retrieve key")
        MagicEnvelope(doc=self.doc, public_key=sender_key, verify=True)

    def build_send(self, entity: BaseEntity, from_user: UserType, to_user_key: RsaKey = None) -> Union[str, Dict]:
        """
        Build POST data for sending out to remotes.

        :param entity: The outbound ready entity for this protocol.
        :param from_user: The user sending this payload. Must have ``private_key`` and ``id`` properties.
        :param to_user_key: (Optional) Public key of user we're sending a private payload to.
        :returns: dict or string depending on if private or public payload.
        """
        if entity.outbound_doc is not None:
            # Use pregenerated outbound document
            xml = entity.outbound_doc
        else:
            xml = entity.to_xml()
        me = MagicEnvelope(etree.tostring(xml), private_key=from_user.rsa_private_key, author_handle=from_user.handle)
        rendered = me.render()
        if to_user_key:
            return EncryptedPayload.encrypt(rendered, to_user_key)
        return rendered
