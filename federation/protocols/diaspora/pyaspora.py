from base64 import b64decode, b64encode, urlsafe_b64decode, urlsafe_b64encode
from Crypto.Cipher import AES, PKCS1_v1_5
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Signature import PKCS1_v1_5 as PKCSSign
from json import dumps, loads
from lxml import etree
from re import match as re_match, sub as re_sub
from sys import version as python_version
from urllib.parse import quote as url_quote, quote_plus, unquote_plus, \
    urlencode, urlparse
from urllib.request import build_opener, HTTPRedirectHandler, Request, \
    urlopen


# The namespace for the Diaspora envelope
PROTOCOL_NS = "https://joindiaspora.com/protocol"


# Our user agent
USER_AGENT = 'social-federation/diaspora/0.1'


class DiasporaMessageBuilder:
    """
    A class to take a payload message and wrap it in the outer Diaspora
    message format, including building the envelope and performing the
    encryption.

    Much of the terminology in the method names comes directly from the
    protocol documentation at:
    https://github.com/diaspora/diaspora/wiki/Federation-Protocol-Overview
    """
    def __init__(self, message, author_username, private_key):
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
        if python_version < '3':
            return ''.join([chr(v) for v in vals])
        else:
            return bytes(vals)

    def post(self, url, recipient_public_key):
        """
        Actually send the message to an HTTP/HTTPs endpoint.
        """
        xml = url_quote(
            self.create_salmon_envelope(recipient_public_key))
        data = urlencode({
            'xml': xml
        })
        req = Request(url)
        req.add_header('User-Agent', USER_AGENT)
        return urlopen(req, data.encode("ascii"), timeout=60)


class DiasporaMessageParser:
    """
    After CherryPy has received a Salmon Slap, this decodes it to extract the
    payload, validating the signature.
    """

    def __init__(self, contact_fetcher):
        self.contact_fetcher = contact_fetcher

    def decode(self, raw, key):
        """
        Extract the envelope XML from its wrapping.
        """
        # It has already been URL-decoded once by Flask
        xml = unquote_plus(raw)
        return self.process_salmon_envelope(xml, key)

    def process_salmon_envelope(self, xml, key):
        """
        Given the Slap XML, extract out the author and payload.
        """
        xml = xml.lstrip().encode("utf-8")
        doc = etree.fromstring(xml)
        header = doc.find(".//{"+PROTOCOL_NS+"}header")
        if header is not None:  # Public
            encrypted = False
            sender = header.find(".//{"+PROTOCOL_NS+"}author_id").text
        else:
            header = self.parse_header(
                doc.find(".//{"+PROTOCOL_NS+"}encrypted_header").text,
                key)
            encrypted = True
            sender = header.find(".//author_id").text

        sending_contact = self.contact_fetcher(sender).contact
        body = doc.find(
            ".//{http://salmon-protocol.org/ns/magic-env}data").text
        sig = doc.find(
            ".//{http://salmon-protocol.org/ns/magic-env}sig").text
        self.verify_signature(sending_contact, body, sig.encode('ascii'))

        if encrypted:
            inner_iv = b64decode(header.find(".//iv").text.encode("ascii"))
            inner_key = b64decode(
                header.find(".//aes_key").text.encode("ascii"))

            decrypter = AES.new(inner_key, AES.MODE_CBC, inner_iv)
            body = b64decode(urlsafe_b64decode(body.encode("ascii")))
            body = decrypter.decrypt(body)
            body = self.pkcs7_unpad(body)
        else:
            body = urlsafe_b64decode(body.encode("ascii"))

        return body, sending_contact

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


class WebfingerRequest(object):
    '''
    A request for WebFinder information for a particular Diaspora user.
    '''

    def __init__(self, email):
        '''
        Create a request for information to Diaspora user with username
        <email> (of form "user@host").
        '''
        self.request_email = email
        self.secure = True
        self.normalise_email()

    def fetch(self):
        """
        Fetch the WebFinger profile and return the XML document.
        """
        template_url = self._get_template()
        target_url = re_sub(
            '\{uri\}',
            quote_plus(
                self.request_email.scheme + ':' + self.request_email.path
            ),
            template_url
        )
        req = Request(target_url)
        req.add_header('User-Agent', USER_AGENT)
        return etree.parse(urlopen(req))

    def _get_template(self):
        """
        Given the HostMeta, extract the template URL for the main WebFinger
        information.
        """
        tree = self.hostmeta.fetch()
        return (
            tree.xpath(
                "//x:Link[@rel='lrdd']/@template",
                namespaces={'x': 'http://docs.oasis-open.org/ns/xri/xrd-1.0'}
            )
        )[0]

    def normalise_email(self):
        """
        Normalise the email address provides into an account URL
        """
        url = urlparse(self.request_email, "acct")
        if url.scheme != "acct":
            raise TypeError()
        self.request_email = url
        match = re_match('.*\@(.*)', url.path)
        self.hostmeta = HostMeta(match.group(1))


class HostMeta(object):
    '''
    A request for a HostMeta on a remote server.
    '''

    def __init__(self, hostname):
        '''
        Create a fetch request for host name <hostname>.
        '''
        self.request_host = hostname
        self.secure = True

    def _build_url(self, scheme):
        """
        Create the URL to fetch on the remote host.
        """
        return scheme + "://" + self.request_host + "/.well-known/host-meta"

    def _open_url(self, url):
        """
        Create the connection to the remote host.
        """
        request = Request(url)
        opener = build_opener(RedirectTrackingHandler())
        opener.addheaders = [('User-Agent', USER_AGENT)]
        return opener.open(request, timeout=5)

    def _get_connection(self):
        """
        Try to connect to the remote host, using HTTPS and falling back to
        HTTP. Track whether any steps in fetching it (redirects) are insecure.
        """
        try:
            res = self._open_url(self._build_url("https"))
        except:
            self.secure = False
            res = self._open_url(self._build_url("http"))

        if self.secure and hasattr(res, "redirected_via"):
            # Check redirections
            for u in res.redirected_via:
                up = urlparse(u)
                if up.scheme != "https":
                    self.secure = False
                    break

        return res

    def fetch(self):
        """
        Fetch and return the HostMeta XML document.
        """
        conn = self._get_connection()
        tree = etree.parse(conn)
        if not self.secure:
            self.validate_signature(tree)

        return tree

    def validate_signature(self, tree):
        """
        If any part of fetching the HostMeta occurs insecurely (eg. over HTTP)
        then attempt to fetch and validate the signature of the HostMeta).
        """
        # TODO fixme cannot use flask.current_app here
        # assert current_app.config.get('ALLOW_INSECURE_COMPAT', False), \
        #     "Configuration doesn't permit HTTP lookup"
        pass


class RedirectTrackingHandler(HTTPRedirectHandler):
    """
    Utility class that spots if we are redirected via a non-HTTPS site.
    """
    def http_error_301(self, req, fp, code, msg, headers):
        new_url = req.get_full_url()
        result = HTTPRedirectHandler.http_error_301(
            self, req, fp, code, msg, headers)
        if not hasattr(result, "redirected_via"):
            result.redirected_via = []
        result.redirected_via.append(new_url)

    def http_error_302(self, req, fp, code, msg, headers):
        previous_url = req.url
        result = HTTPRedirectHandler.http_error_302(
            self, req, fp, code, msg, headers)
        if not hasattr(result, "redirected_via"):
            result.redirected_via = []
        result.redirected_via.append(previous_url)
