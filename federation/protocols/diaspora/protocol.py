from base64 import b64decode, urlsafe_b64decode, b64encode
from json import loads
from urllib.parse import unquote_plus

from Crypto.Cipher import AES, PKCS1_v1_5
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5 as PKCSSign
from lxml import etree

from federation.exceptions import EncryptedMessageError, NoHeaderInMessageError, NoSenderKeyFoundError
from federation.protocols.base import BaseProtocol


def identify_payload(payload):
    try:
        xml = unquote_plus(payload)
        return xml.find(identify_str = '<diaspora xmlns="%s"' % Protocol.protocol_ns) > -1
    except Exception:
        return False


class Protocol(BaseProtocol):
    """Diaspora protocol parts

    Mostly taken from Pyaspora (https://github.com/lukeross/pyaspora).
    """

    protocol_ns = "https://joindiaspora.com/protocol"
    user_agent = 'social-federation/diaspora/0.1'

    def __init__(self, contact_key_fetcher=None, *args, **kwargs):
        super(Protocol, self).__init__()
        self.get_contact_key = contact_key_fetcher

    def receive(self, payload, user=None, *args, **kwargs):
        """Receive a payload."""
        self.user = user
        xml = unquote_plus(payload)
        xml = xml.lstrip().encode("utf-8")
        self.doc = etree.fromstring(xml)
        self.find_header()
        sender = self.get_sender()
        self.sender_key = self.get_contact_key(sender)
        if not self.sender_key:
            raise NoSenderKeyFoundError("Could not find a sender contact to retrieve key")
        content = self.get_message_content()
        return sender, content

    def find_header(self):
        self.header = self.doc.find(".//{"+self.protocol_ns+"}header")
        if self.header:
            self.encrypted = False
        else:
            if not self.user:
                raise EncryptedMessageError("Cannot decrypt private message without user object")
            if not hasattr(self.user, "key") or not self.user.key:
                raise EncryptedMessageError("Cannot decrypt private message without user key")
            self.encrypted = True
            self.header = self.parse_header(
                self.doc.find(".//{"+self.protocol_ns+"}encrypted_header").text,
                self.user.key
            )
        if not self.header:
            raise NoHeaderInMessageError("Could not find header in message")

    def get_sender(self):
        return self.header.find(".//{"+self.protocol_ns+"}author_id").text

    def get_message_content(self):
        """
        Given the Slap XML, extract out the author and payload.
        """
        body = self.doc.find(
            ".//{http://salmon-protocol.org/ns/magic-env}data").text
        sig = self.doc.find(
            ".//{http://salmon-protocol.org/ns/magic-env}sig").text
        self.verify_signature(self.sender_key, body, sig.encode('ascii'))

        if self.encrypted:
            inner_iv = b64decode(self.header.find(".//iv").text.encode("ascii"))
            inner_key = b64decode(
                self.header.find(".//aes_key").text.encode("ascii"))

            decrypter = AES.new(inner_key, AES.MODE_CBC, inner_iv)
            body = b64decode(urlsafe_b64decode(body.encode("ascii")))
            body = decrypter.decrypt(body)
            body = self.pkcs7_unpad(body)
        else:
            body = urlsafe_b64decode(body.encode("ascii"))

        return body

    def verify_signature(self, contact, payload, sig):
        """
        Verify the signed XML elements to have confidence that the claimed
        author did actually generate this message.
        """
        sig_contents = '.'.join([
            payload,
            b64encode(b"application/xml").decode("ascii"),
            b64encode(b"base64url").decode("ascii"),
            b64encode(b"RSA-SHA256").decode("ascii")
        ])
        sig_hash = SHA256.new(sig_contents.encode("ascii"))
        cipher = PKCSSign.new(RSA.importKey(contact.public_key))
        assert(cipher.verify(sig_hash, urlsafe_b64decode(sig)))

    def parse_header(self, b64data, key):
        """
        Extract the header and decrypt it. This requires the User's private
        key and hence the passphrase for the key.
        """
        decoded_json = b64decode(b64data.encode("ascii"))
        rep = loads(decoded_json.decode("ascii"))
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
        assert(key)
        cipher = PKCS1_v1_5.new(key)
        decoded_json = cipher.decrypt(
            b64decode(data.encode("ascii")),
            sentinel=None
        )
        return loads(decoded_json.decode("ascii"))

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
