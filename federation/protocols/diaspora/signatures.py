from base64 import b64decode, b64encode

from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5


def get_element_child_info(doc, attr):
    """Get information from child elements of this elementas a list since order is important.

    Don't include signature tags.

    :param doc: XML element
    :param attr: Attribute to get from the elements, for example "tag" or "text".
    """
    props = []
    for child in doc:
        if child.tag not in ["author_signature", "parent_author_signature"]:
            props.append(getattr(child, attr))
    return props


def _create_signature_hash(doc):
    props = get_element_child_info(doc, "text")
    content = ";".join(props)
    return SHA256.new(content.encode("utf-8"))


def verify_relayable_signature(public_key, doc, signature):
    """
    Verify the signed XML elements to have confidence that the claimed
    author did actually generate this message.
    """
    sig_hash = _create_signature_hash(doc)
    cipher = PKCS1_v1_5.new(RSA.importKey(public_key))
    return cipher.verify(sig_hash, b64decode(signature))


def create_relayable_signature(private_key, doc):
    sig_hash = _create_signature_hash(doc)
    cipher = PKCS1_v1_5.new(private_key)
    return b64encode(cipher.sign(sig_hash)).decode("ascii")
