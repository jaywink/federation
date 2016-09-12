from base64 import urlsafe_b64encode, b64encode

from Crypto.Hash import SHA256
from Crypto.Signature import PKCS1_v1_5 as PKCSSign
from lxml import etree


class MagicEnvelope(object):
    """Diaspora protocol magic envelope.

    See: http://diaspora.github.io/diaspora_federation/federation/magicsig.html
    """

    nsmap = {
        'me': 'http://salmon-protocol.org/ns/magic-env'
    }

    def __init__(self, message, private_key, author_handle, wrap_payload=False):
        """
        Args:
            wrap_payload (bool) - Whether to wrap the message in <XML><post></post></XML>.
                This is part of the legacy Diaspora protocol which will be removed in the future. (default False)
        """
        self.message = message
        self.private_key = private_key
        self.author_handle = author_handle
        self.wrap_payload = wrap_payload
        self.doc = None
        self.payload = None

    def _encode_payload(self):
        """Encode the payload and wrap it to 60 char lines."""
        self.payload = urlsafe_b64encode(self.payload).decode("ascii")
        self.payload = '\n'.join(
            [self.payload[start:start + 60] for start in range(0, len(self.payload), 60)]
        )
        self.payload += "\n"
        return self.payload

    def create_payload(self):
        """Create the payload doc.

        Returns:
            bytes
        """
        doc = etree.fromstring(self.message)
        if self.wrap_payload:
            wrap = etree.Element("XML")
            post = etree.SubElement(wrap, "post")
            post.append(doc)
            doc = wrap
        self.payload = etree.tostring(doc, encoding="utf-8")
        return self.payload

    def _build_signature(self):
        """Create the signature using the private key."""
        sig_contents = \
            self.payload + "." + \
            b64encode(b"application/xml").decode("ascii") + "." + \
            b64encode(b"base64url").decode("ascii") + "." + \
            b64encode(b"RSA-SHA256").decode("ascii")
        sig_hash = SHA256.new(sig_contents.encode("ascii"))
        cipher = PKCSSign.new(self.private_key)
        sig = urlsafe_b64encode(cipher.sign(sig_hash))
        key_id = urlsafe_b64encode(bytes(self.author_handle, encoding="utf-8"))
        return sig, key_id

    def build(self):
        self.doc = etree.Element("{%s}env" % self.nsmap["me"], nsmap=self.nsmap)
        etree.SubElement(self.doc, "{%s}encoding" % self.nsmap["me"]).text = 'base64url'
        etree.SubElement(self.doc, "{%s}alg" % self.nsmap["me"]).text = 'RSA-SHA256'
        self.create_payload()
        self._encode_payload()
        etree.SubElement(self.doc, "{%s}data" % self.nsmap["me"],
                         {"type": "application/xml"}).text = self.payload
        signature, key_id = self._build_signature()
        etree.SubElement(self.doc, "{%s}sig" % self.nsmap["me"], key_id=key_id).text = signature
        return self.doc

    def render(self):
        if self.doc is None:
            self.build()
        return etree.tostring(self.doc, encoding="unicode")
