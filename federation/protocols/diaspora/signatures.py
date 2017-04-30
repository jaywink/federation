from base64 import urlsafe_b64decode, urlsafe_b64encode

from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5


def _create_signature_hash(doc):
    props = []
    for child in doc:
        if child.tag not in ["author_signature", "parent_author_signature"]:
            props.append(child.text)
    content = ";".join(props)
    return SHA256.new(content.encode("ascii"))


def verify_relayable_signature(public_key, doc, signature):
    """
    Verify the signed XML elements to have confidence that the claimed
    author did actually generate this message.
    """
    sig_hash = _create_signature_hash(doc)
    cipher = PKCS1_v1_5.new(RSA.importKey(public_key))
    return cipher.verify(sig_hash, urlsafe_b64decode(signature))


def create_relayable_signature(private_key, doc):
    sig_hash = _create_signature_hash(doc)
    cipher = PKCS1_v1_5.new(private_key)
    return urlsafe_b64encode(cipher.sign(sig_hash)).decode("ascii")
