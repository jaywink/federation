from base64 import urlsafe_b64encode, b64encode, urlsafe_b64decode

from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from lxml import etree

from federation.exceptions import SignatureVerificationError
from federation.utils.diaspora import fetch_public_key
from federation.utils.text import decode_if_bytes

NAMESPACE = "http://salmon-protocol.org/ns/magic-env"


class MagicEnvelope:
    """Diaspora protocol magic envelope.

    Can be used to construct and deconstruct MagicEnvelope documents.

    When constructing, the following parameters should be given:
    * message
    * private_key
    * author_handle

    When deconstructing, the following should be given:
    * payload
    * public_key (optional, will be fetched if not given, using either 'sender_key_fetcher' or remote server)

    Upstream specification: http://diaspora.github.io/diaspora_federation/federation/magicsig.html
    """

    nsmap = {
        "me": NAMESPACE,
    }

    def __init__(self, message=None, private_key=None, author_handle=None, wrap_payload=False, payload=None,
                 public_key=None, sender_key_fetcher=None, verify=False, doc=None):
        """
        All parameters are optional. Some are required for signing, some for opening.

        :param message: Message string. Required to create a MagicEnvelope document.
        :param private_key: Private key RSA object.
        :param author_handle: Author signing the Magic Envelope, owns the private key.
        :param wrap_payload: - Boolean, whether to wrap the message in <XML><post></post></XML>.
            This is part of the legacy Diaspora protocol which will be removed in the future. (default False)
        :param payload: Magic Envelope payload as str or bytes.
        :param public_key: Author public key in str format.
        :param sender_key_fetcher: Function to use to fetch sender public key, if public key not given. Will fall back
            to network fetch of the profile and the key. Function must take handle as only parameter and return
            a public key string.
        :param verify: Verify after creating object, defaults to False.
        :param doc: MagicEnvelope document.
        """
        self._message = message
        self.private_key = private_key
        self.author_handle = author_handle
        self.wrap_payload = wrap_payload
        self.payload = payload
        self.public_key = public_key
        self.sender_key_fetcher = sender_key_fetcher
        if payload:
            self.extract_payload()
        elif doc is not None:
            self.doc = doc
        else:
            self.doc = None
        if verify:
            self.verify()

    def extract_payload(self):
        payload = decode_if_bytes(self.payload)
        payload = payload.lstrip().encode("utf-8")
        self.doc = etree.fromstring(payload)
        self.author_handle = self.get_sender(self.doc)
        self.message = self.message_from_doc()

    def fetch_public_key(self):
        if self.sender_key_fetcher:
            self.public_key = self.sender_key_fetcher(self.author_handle)
            return
        self.public_key = fetch_public_key(self.author_handle)

    @staticmethod
    def get_sender(doc):
        """Get the key_id from the `sig` element which contains urlsafe_b64encoded Diaspora handle.

        :param doc: ElementTree document
        :returns: Diaspora handle
        """
        key_id = doc.find(".//{%s}sig" % NAMESPACE).get("key_id")
        return urlsafe_b64decode(key_id).decode("utf-8")

    @property
    def message(self):
        return self._message

    @message.setter
    def message(self, value):
        self._message = value

    def message_from_doc(self):
        message = self.doc.find(
            ".//{http://salmon-protocol.org/ns/magic-env}data").text
        return urlsafe_b64decode(message.encode("ascii"))

    def create_payload(self):
        """Create the payload doc.

        Returns:
            str
        """
        doc = etree.fromstring(self.message)
        if self.wrap_payload:
            wrap = etree.Element("XML")
            post = etree.SubElement(wrap, "post")
            post.append(doc)
            doc = wrap
        self.payload = etree.tostring(doc, encoding="utf-8")
        self.payload = urlsafe_b64encode(self.payload).decode("ascii")
        return self.payload

    def _build_signature(self):
        """Create the signature using the private key."""
        sig_contents = \
            self.payload + "." + \
            b64encode(b"application/xml").decode("ascii") + "." + \
            b64encode(b"base64url").decode("ascii") + "." + \
            b64encode(b"RSA-SHA256").decode("ascii")
        sig_hash = SHA256.new(sig_contents.encode("ascii"))
        cipher = PKCS1_v1_5.new(self.private_key)
        sig = urlsafe_b64encode(cipher.sign(sig_hash))
        key_id = urlsafe_b64encode(bytes(self.author_handle, encoding="utf-8"))
        return sig, key_id

    def build(self):
        self.doc = etree.Element("{%s}env" % NAMESPACE, nsmap=self.nsmap)
        etree.SubElement(self.doc, "{%s}encoding" % NAMESPACE).text = 'base64url'
        etree.SubElement(self.doc, "{%s}alg" % NAMESPACE).text = 'RSA-SHA256'
        self.create_payload()
        etree.SubElement(self.doc, "{%s}data" % NAMESPACE, {"type": "application/xml"}).text = self.payload
        signature, key_id = self._build_signature()
        etree.SubElement(self.doc, "{%s}sig" % NAMESPACE, key_id=key_id).text = signature
        return self.doc

    def render(self):
        if self.doc is None:
            self.build()
        return etree.tostring(self.doc, encoding="unicode")

    def verify(self):
        """Verify Magic Envelope document against public key."""
        if not self.public_key:
            self.fetch_public_key()
        data = self.doc.find(".//{http://salmon-protocol.org/ns/magic-env}data").text
        sig = self.doc.find(".//{http://salmon-protocol.org/ns/magic-env}sig").text
        sig_contents = '.'.join([
            data,
            b64encode(b"application/xml").decode("ascii"),
            b64encode(b"base64url").decode("ascii"),
            b64encode(b"RSA-SHA256").decode("ascii")
        ])
        sig_hash = SHA256.new(sig_contents.encode("ascii"))
        cipher = PKCS1_v1_5.new(RSA.importKey(self.public_key))
        if not cipher.verify(sig_hash, urlsafe_b64decode(sig)):
            raise SignatureVerificationError("Signature cannot be verified using the given public key")
