from __future__ import print_function
import base64
import six

from Crypto.Hash import HMAC
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from .sign_algorithms import SignAlgorithm
from .utils import *

DEFAULT_ALGORITHM = "hs2019"


class Signer(object):
    """
    When using an RSA algo, the secret is a PEM-encoded private key.
    When using an HMAC algo, the secret is the HMAC signing secret.

    Password-protected keyfiles are not supported.
    """

    def __init__(self, secret, algorithm=None, sign_algorithm=None):
        if algorithm is None:
            algorithm = DEFAULT_ALGORITHM

        assert algorithm in ALGORITHMS, "Unknown algorithm"

        if sign_algorithm is not None and not issubclass(type(sign_algorithm), SignAlgorithm):
            raise HttpSigException("Unsupported digital signature algorithm")

        if algorithm == DEFAULT_ALGORITHM and sign_algorithm is None:
            raise HttpSigException("Required sign algorithm for {} algorithm not set".format(DEFAULT_ALGORITHM))

        if isinstance(secret, six.string_types):
            secret = secret.encode("ascii")

        self._rsa = None
        self._hash = None
        self.algorithm = algorithm
        self.secret = secret

        if "-" in algorithm:
            self.sign_algorithm, self.hash_algorithm = algorithm.split('-')
        elif algorithm == "hs2019":
            assert sign_algorithm is not None, "Required digital signature algorithm not specified"
            self.sign_algorithm = sign_algorithm

        if self.sign_algorithm == 'rsa':
            try:
                rsa_key = RSA.importKey(secret)
                self._rsa = PKCS1_v1_5.new(rsa_key)
                self._hash = HASHES[self.hash_algorithm]
            except ValueError:
                raise HttpSigException("Invalid key.")

        elif self.sign_algorithm == 'hmac':
            self._hash = HMAC.new(secret,
                                  digestmod=HASHES[self.hash_algorithm])

    def _sign_rsa(self, data):
        if isinstance(data, six.string_types):
            data = data.encode("ascii")
        h = self._hash.new()
        h.update(data)
        return self._rsa.sign(h)

    def _sign_hmac(self, data):
        if isinstance(data, six.string_types):
            data = data.encode("ascii")
        hmac = self._hash.copy()
        hmac.update(data)
        return hmac.digest()

    def sign(self, data):
        if isinstance(data, six.string_types):
            data = data.encode("ascii")
        signed = None
        if self._rsa:
            signed = self._sign_rsa(data)
        elif self._hash:
            signed = self._sign_hmac(data)
        elif issubclass(type(self.sign_algorithm), SignAlgorithm):
            signed = self.sign_algorithm.sign(self.secret, data)
        if not signed:
            raise SystemError('No valid encryptor found.')
        return base64.b64encode(signed).decode("ascii")


class HeaderSigner(Signer):
    """
    Generic object that will sign headers as a dictionary using the
        http-signature scheme.
    https://github.com/joyent/node-http-signature/blob/master/http_signing.md

    :arg key_id:    the mandatory label indicating to the server which secret
        to use
    :arg secret:    a PEM-encoded RSA private key or an HMAC secret (must
        match the algorithm)
    :param algorithm: one of the seven specified algorithms
    :param sign_algorithm: required for 'hs2019' algorithm. Sign algorithm for the secret
    :param headers:   a list of http headers to be included in the signing
        string, defaulting to ['date'].
    :param sign_header: header used to include signature, defaulting to
       'authorization'.
    """

    def __init__(self, key_id, secret, algorithm=None, sign_algorithm=None, headers=None, created=None, expires=None, sign_header='Signature'):
        if algorithm is None:
            algorithm = DEFAULT_ALGORITHM
        if not key_id:
            raise ValueError("key_id can't be empty")

        if len(key_id) > 100000:
            raise ValueError("key_id cant be larger than 100000 chars")

        if not secret:
            raise ValueError("secret can't be empty")

        if len(secret) > 100000:
            raise ValueError("secret cant be larger than 100000 chars")

        super(HeaderSigner, self).__init__(secret=secret, algorithm=algorithm, sign_algorithm=sign_algorithm)
        self.headers = headers or ['date']
        self.signature_template = build_signature_template(
            key_id, algorithm, headers, created, expires, sign_header)
        self.sign_header = sign_header

    def sign(self, headers, host=None, method=None, path=None, created=None, expires=None):
        """
        Add Signature Authorization header to case-insensitive header dict.

        `headers` is a case-insensitive dict of mutable headers.
        `host` is a override for the 'host' header (defaults to value in
            headers).
        `method` is the HTTP method (required when using '(request-target)').
        `path` is the HTTP path (required when using '(request-target)').
        """
        headers = CaseInsensitiveDict(headers)
        required_headers = self.headers or ['date']
        signable = generate_message(
            required_headers, headers, host, method, path, created, expires)

        signature = super(HeaderSigner, self).sign(signable)
        headers[self.sign_header] = self.signature_template % signature

        return headers
