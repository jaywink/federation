from base64 import b64decode, urlsafe_b64decode, b64encode, urlsafe_b64encode
from json import loads, dumps
from urllib.parse import unquote_plus, quote_plus, urlencode

from Crypto.Cipher import AES, PKCS1_v1_5
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Signature import PKCS1_v1_5 as PKCSSign
from lxml import etree

from federation.entities.diaspora.generators import EntityConverter
from federation.exceptions import EncryptedMessageError, NoHeaderInMessageError, NoSenderKeyFoundError
from federation.protocols.base import BaseProtocol


PROTOCOL_NAME = "diaspora"
PROTOCOL_NS = "https://joindiaspora.com/protocol"
USER_AGENT = 'social-federation/diaspora/0.1'


def identify_payload(payload):
    try:
        xml = unquote_plus(payload)
        return xml.find('<diaspora xmlns="%s"' % PROTOCOL_NS) > -1
    except Exception:
        return False


class Protocol(BaseProtocol):
    """Diaspora protocol parts

    Mostly taken from Pyaspora (https://github.com/lukeross/pyaspora).
    """
    def receive(self, payload, user=None, sender_key_fetcher=None, *args, **kwargs):
        """Receive a payload."""
        self.user = user
        self.get_contact_key = sender_key_fetcher
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
        self.header = self.doc.find(".//{"+PROTOCOL_NS+"}header")
        if self.header:
            self.encrypted = False
        else:
            if not self.user:
                raise EncryptedMessageError("Cannot decrypt private message without user object")
            if not hasattr(self.user, "key") or not self.user.key:
                raise EncryptedMessageError("Cannot decrypt private message without user key")
            self.encrypted = True
            self.header = self.parse_header(
                self.doc.find(".//{"+PROTOCOL_NS+"}encrypted_header").text,
                self.user.key
            )
        if not self.header:
            raise NoHeaderInMessageError("Could not find header in message")

    def get_sender(self):
        return self.header.find(".//{"+PROTOCOL_NS+"}author_id").text

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

    def build_send(self, from_user, to_user, entity, *args, **kwargs):
        """Build POST data for sending out to remotes."""
        converter = EntityConverter(entity)
        xml = converter.convert_to_xml()
        self.init_message(xml, from_user.handle, from_user.private_key)
        xml = quote_plus(
            self.create_salmon_envelope(to_user.key))
        data = urlencode({
            'xml': xml
        })
        return data

    def init_message(self, message, author_username, private_key):
        """
        Build a Diaspora message and prepare to send the payload <message>,
        authored by Contact <author>. The receipient is specified later, so
        that the same message can be sent to several people without needing to
        keep re-encrypting the inner.
        """

        # We need an AES key for the envelope
        self.inner_iv = get_random_bytes(AES.block_size)
        self.inner_key = get_random_bytes(32)
        self.inner_encrypter = AES.new(
            self.inner_key, AES.MODE_CBC, self.inner_iv)

        # ...and one for the payload message
        self.outer_iv = get_random_bytes(AES.block_size)
        self.outer_key = get_random_bytes(32)
        self.outer_encrypter = AES.new(
            self.outer_key, AES.MODE_CBC, self.outer_iv)
        self.message = message
        self.author_username = author_username
        self.private_key = private_key

    def xml_to_string(self, doc, xml_declaration=False):
        """
        Utility function to turn an XML document to a string. This is
        abstracted out so that pretty-printing can be turned on and off in one
        place.
        """
        return etree.tostring(
            doc,
            xml_declaration=xml_declaration,
            pretty_print=True,
            encoding="UTF-8"
        )

    def create_decrypted_header(self):
        """
        Build the XML document for the header. The header contains the key
        used to encrypt the message body.
        """
        decrypted_header = etree.Element('decrypted_header')
        etree.SubElement(decrypted_header, "iv").text = \
            b64encode(self.inner_iv)
        etree.SubElement(decrypted_header, "aes_key").text = \
            b64encode(self.inner_key)
        etree.SubElement(decrypted_header, "author_id").text = \
            self.author_username
        return self.xml_to_string(decrypted_header)

    def create_public_header(self):
        decrypted_header = etree.Element('header')
        etree.SubElement(decrypted_header, "author_id").text = \
            self.author_username
        return decrypted_header

    def create_ciphertext(self):
        """
        Encrypt the header.
        """
        to_encrypt = self.pkcs7_pad(
            self.create_decrypted_header(),
            AES.block_size
        )
        out = self.outer_encrypter.encrypt(to_encrypt)
        return out

    def create_outer_aes_key_bundle(self):
        """
        Record the information on the key used to encrypt the header.
        """
        d = dumps({
            "iv": b64encode(self.outer_iv).decode("ascii"),
            "key": b64encode(self.outer_key).decode("ascii")
        })
        return d

    def create_encrypted_outer_aes_key_bundle(self, recipient_rsa):
        """
        The Outer AES Key Bundle is encrypted with the receipient's public
        key, so only the receipient can decrypt the header.
        """
        cipher = PKCS1_v1_5.new(recipient_rsa)
        return cipher.encrypt(
            self.create_outer_aes_key_bundle().encode("utf-8"))

    def create_encrypted_header_json_object(self, public_key):
        """
        The actual header and the encrypted outer (header) key are put into a
        document together.
        """
        aes_key = b64encode(self.create_encrypted_outer_aes_key_bundle(
            public_key)).decode("ascii")
        ciphertext = b64encode(self.create_ciphertext()).decode("ascii")

        d = dumps({
            "aes_key": aes_key,
            "ciphertext": ciphertext
        })
        return d

    def create_encrypted_header(self, public_key):
        """
        The "encrypted header JSON object" is dropped into some XML. I am not
        sure what this is for, but is required to interact.
        """
        doc = etree.Element("encrypted_header")
        doc.text = b64encode(self.create_encrypted_header_json_object(
            public_key).encode("ascii"))
        return doc

    def create_payload(self):
        """
        Wrap the actual payload message in the standard XML wrapping.
        """
        doc = etree.Element("XML")
        inner = etree.SubElement(doc, "post")
        if isinstance(self.message, str):
            inner.text = self.message
        else:
            inner.append(self.message)
        return self.xml_to_string(doc)

    def create_encrypted_payload(self):
        """
        Encrypt the payload XML with the inner (body) key.
        """
        to_encrypt = self.pkcs7_pad(self.create_payload(), AES.block_size)
        return self.inner_encrypter.encrypt(to_encrypt)

    def create_salmon_envelope(self, recipient_public_key):
        """
        Build the whole message, pulling together the encrypted payload and the
        encrypted header. Selected elements are signed by the author so that
        tampering can be detected.
        """
        nsmap = {
            None: PROTOCOL_NS,
            'me': 'http://salmon-protocol.org/ns/magic-env'
        }
        doc = etree.Element("{%s}diaspora" % nsmap[None], nsmap=nsmap)
        if recipient_public_key:
            doc.append(self.create_encrypted_header(recipient_public_key))
        else:
            doc.append(self.create_public_header())
        env = etree.SubElement(doc, "{%s}env" % nsmap["me"])
        etree.SubElement(env, "{%s}encoding" % nsmap["me"]).text = 'base64url'
        etree.SubElement(env, "{%s}alg" % nsmap["me"]).text = 'RSA-SHA256'
        if recipient_public_key:
            payload = urlsafe_b64encode(b64encode(
                self.create_encrypted_payload())).decode("ascii")
        else:
            payload = urlsafe_b64encode(self.create_payload()).decode("ascii")
        # Split every 60 chars
        payload = '\n'.join([payload[start:start+60]
                             for start in range(0, len(payload), 60)])
        payload = payload + "\n"
        etree.SubElement(env, "{%s}data" % nsmap["me"],
                         {"type": "application/xml"}).text = payload
        sig_contents = payload + "." + \
            b64encode(b"application/xml").decode("ascii") + "." + \
            b64encode(b"base64url").decode("ascii") + "." + \
            b64encode(b"RSA-SHA256").decode("ascii")
        sig_hash = SHA256.new(sig_contents.encode("ascii"))
        cipher = PKCSSign.new(self.private_key)
        sig = urlsafe_b64encode(cipher.sign(sig_hash))
        etree.SubElement(env, "{%s}sig" % nsmap["me"]).text = sig
        return self.xml_to_string(doc)

    def pkcs7_pad(self, inp, block_size):
        """
        Using the PKCS#7 padding scheme, pad <inp> to be a multiple of
        <block_size> bytes. Ruby's AES encryption pads with this scheme, but
        pycrypto doesn't support it.
        """
        val = block_size - len(inp) % block_size
        if val == 0:
            return inp + (self.array_to_bytes([block_size]) * block_size)
        else:
            return inp + (self.array_to_bytes([val]) * val)

    def array_to_bytes(self, vals):
        return bytes(vals)
