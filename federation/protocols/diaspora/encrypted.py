import json
from base64 import b64decode, b64encode

from Crypto.Cipher import PKCS1_v1_5, AES
from Crypto.Random import get_random_bytes
from lxml import etree


def pkcs7_unpad(data):
    """Remove the padding bytes that were added at point of encryption."""
    if isinstance(data, str):
        return data[0:-ord(data[-1])]
    else:
        return data[0:-data[-1]]


class EncryptedPayload:
    """Diaspora encrypted JSON payloads."""

    @staticmethod
    def decrypt(payload, private_key):
        """Decrypt an encrypted JSON payload and return the Magic Envelope document inside."""
        cipher = PKCS1_v1_5.new(private_key)
        aes_key_str = cipher.decrypt(b64decode(payload.get("aes_key")), sentinel=None)
        aes_key = json.loads(aes_key_str.decode("utf-8"))
        key = b64decode(aes_key.get("key"))
        iv = b64decode(aes_key.get("iv"))
        encrypted_magic_envelope = b64decode(payload.get("encrypted_magic_envelope"))
        encrypter = AES.new(key, AES.MODE_CBC, iv)
        content = encrypter.decrypt(encrypted_magic_envelope)
        return etree.fromstring(pkcs7_unpad(content))

    @staticmethod
    def get_aes_key_json():
        iv = get_random_bytes(AES.block_size)
        key = get_random_bytes(32)
        encrypter = AES.new(key, AES.MODE_CBC, iv)
        return {
            "key": b64encode(key),
            "iv": b64encode(iv),
        }, encrypter

    @staticmethod
    def encrypt(payload, public_key):
        """
        Encrypt a payload using an encrypted JSON wrapper.

        See: <insert link to docs>

        :param payload: Payload document as a string.
        :param public_key: Public key of recipient as an RSA object.
        :return: Encrypted JSON wrapper as dict.
        """
        aes_key_json, encrypter = EncryptedPayload.get_aes_key_json()
        encrypted_me = encrypter.encrypt(payload)
        cipher = PKCS1_v1_5.new(public_key)
        aes_key = cipher.encrypt(aes_key_json)
        return {
            "aes_key": b64encode(aes_key),
            "encrypted_magic_envelope": b64encode(encrypted_me),
        }
