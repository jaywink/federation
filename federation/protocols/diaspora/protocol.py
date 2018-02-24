import json
import logging
from base64 import b64decode, urlsafe_b64decode
from urllib.parse import unquote_plus, unquote

from Crypto.Cipher import AES, PKCS1_v1_5
from lxml import etree

from federation.exceptions import EncryptedMessageError, NoSenderKeyFoundError
from federation.protocols.base import BaseProtocol
from federation.protocols.diaspora.encrypted import EncryptedPayload
from federation.protocols.diaspora.magic_envelope import MagicEnvelope
from federation.utils.diaspora import fetch_public_key
from federation.utils.text import decode_if_bytes, encode_if_text

logger = logging.getLogger("federation")

PROTOCOL_NAME = "diaspora"
PROTOCOL_NS = "https://joindiaspora.com/protocol"
MAGIC_ENV_TAG = "{http://salmon-protocol.org/ns/magic-env}env"


def identify_payload(payload):
    """Try to identify whether this is a Diaspora payload.

    Try first public message. Then private message. The check if this is a legacy payload.
    """
    # Private encrypted JSON payload
    try:
        data = json.loads(decode_if_bytes(payload))
        if "encrypted_magic_envelope" in data:
            return True
    except Exception:
        pass
    # Public XML payload
    try:
        xml = etree.fromstring(encode_if_text(payload))
        if xml.tag == MAGIC_ENV_TAG:
            return True
    except Exception:
        pass
    # Legacy XML payload
    try:
        xml = unquote_plus(payload)
        return xml.find('xmlns="%s"' % PROTOCOL_NS) > -1
    except Exception:
        pass
    return False


class Protocol(BaseProtocol):
    """Diaspora protocol parts

    Mostly taken from Pyaspora (https://github.com/lukeross/pyaspora).
    """
    def __init__(self):
        super().__init__()
        self.encrypted = self.legacy = False

    def get_json_payload_magic_envelope(self, payload):
        """Encrypted JSON payload"""
        private_key = self._get_user_key(self.user)
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

    def receive(self, payload, user=None, sender_key_fetcher=None, skip_author_verification=False):
        """Receive a payload.

        For testing purposes, `skip_author_verification` can be passed. Authorship will not be verified."""
        self.user = user
        self.get_contact_key = sender_key_fetcher
        self.store_magic_envelope_doc(payload)
        # Check for a legacy header
        self.find_header()
        # Open payload and get actual message
        self.content = self.get_message_content()
        # Get sender handle
        self.sender_handle = self.get_sender()
        # Verify the message is from who it claims to be
        if not skip_author_verification:
            self.verify_signature()
        return self.sender_handle, self.content

    def _get_user_key(self, user):
        if not getattr(self.user, "private_key", None):
            raise EncryptedMessageError("Cannot decrypt private message without user key")
        return self.user.private_key

    def find_header(self):
        self.header = self.doc.find(".//{"+PROTOCOL_NS+"}header")
        if self.header != None:
            # Legacy public header found
            self.legacy = True
            return
        if self.doc.find(".//{" + PROTOCOL_NS + "}encrypted_header") == None:
            # No legacy encrypted header found
            return
        self.legacy = True
        if not self.user:
            raise EncryptedMessageError("Cannot decrypt private message without user object")
        user_private_key = self._get_user_key(self.user)
        self.encrypted = True
        self.header = self.parse_header(
            self.doc.find(".//{"+PROTOCOL_NS+"}encrypted_header").text,
            user_private_key
        )

    def get_sender(self):
        if self.legacy:
            return self.get_sender_legacy()
        return MagicEnvelope.get_sender(self.doc)

    def get_sender_legacy(self):
        try:
            return self.header.find(".//{"+PROTOCOL_NS+"}author_id").text
        except AttributeError:
            # Look at the message, try various elements
            message = etree.fromstring(self.content)
            element = message.find(".//author")
            if element is None:
                element = message.find(".//sender_handle")
            if element is None:
                element = message.find(".//diaspora_handle")
            if element is None:
                return None
            return element.text

    def get_message_content(self):
        """
        Given the Slap XML, extract out the payload.
        """
        body = self.doc.find(
            ".//{http://salmon-protocol.org/ns/magic-env}data").text

        if self.encrypted:
            body = self._get_encrypted_body(body)
        else:
            body = urlsafe_b64decode(body.encode("ascii"))

        logger.debug("diaspora.protocol.get_message_content: %s", body)
        return body

    def _get_encrypted_body(self, body):
        """
        Decrypt the body of the payload.
        """
        inner_iv = b64decode(self.header.find(".//iv").text.encode("ascii"))
        inner_key = b64decode(
            self.header.find(".//aes_key").text.encode("ascii"))
        decrypter = AES.new(inner_key, AES.MODE_CBC, inner_iv)
        body = b64decode(urlsafe_b64decode(body.encode("ascii")))
        body = decrypter.decrypt(body)
        body = self.pkcs7_unpad(body)
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

    def parse_header(self, b64data, key):
        """
        Extract the header and decrypt it. This requires the User's private
        key and hence the passphrase for the key.
        """
        decoded_json = b64decode(b64data.encode("ascii"))
        rep = json.loads(decoded_json.decode("ascii"))
        outer_key_details = self.decrypt_outer_aes_key_bundle(
            rep["aes_key"], key)
        header = self.get_decrypted_header(
            b64decode(rep["ciphertext"].encode("ascii")),
            key=b64decode(outer_key_details["key"].encode("ascii")),
            iv=b64decode(outer_key_details["iv"].encode("ascii"))
        )
        return header

    def decrypt_outer_aes_key_bundle(self, data, key):
        """
        Decrypt the AES "outer key" credentials using the private key and
        passphrase.
        """
        if not key:
            raise EncryptedMessageError("No key to decrypt with")
        cipher = PKCS1_v1_5.new(key)
        decoded_json = cipher.decrypt(
            b64decode(data.encode("ascii")),
            sentinel=None
        )
        return json.loads(decoded_json.decode("ascii"))

    def get_decrypted_header(self, ciphertext, key, iv):
        """
        Having extracted the AES "outer key" (envelope) information, actually
        decrypt the header.
        """
        encrypter = AES.new(key, AES.MODE_CBC, iv)
        padded = encrypter.decrypt(ciphertext)
        xml = self.pkcs7_unpad(padded)
        doc = etree.fromstring(xml)
        return doc

    def pkcs7_unpad(self, data):
        """
        Remove the padding bytes that were added at point of encryption.
        """
        if isinstance(data, str):
            return data[0:-ord(data[-1])]
        else:
            return data[0:-data[-1]]

    def build_send(self, entity, from_user, to_user_key=None, *args, **kwargs):
        """
        Build POST data for sending out to remotes.

        :param entity: The outbound ready entity for this protocol.
        :param from_user: The user sending this payload. Must have ``private_key`` and ``handle`` properties.
        :param to_user_key: (Optional) Public key of user we're sending a private payload to.
        :returns: dict or string depending on if private or public payload.
        """
        if entity.outbound_doc is not None:
            # Use pregenerated outbound document
            xml = entity.outbound_doc
        else:
            xml = entity.to_xml()
        me = MagicEnvelope(etree.tostring(xml), private_key=from_user.private_key, author_handle=from_user.handle)
        rendered = me.render()
        if to_user_key:
            return EncryptedPayload.encrypt(rendered, to_user_key)
        return rendered
