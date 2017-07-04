import json
from base64 import b64decode

from Crypto.Cipher import PKCS1_v1_5, AES
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
