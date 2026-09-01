import base64

import six
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_PSS
from Crypto.Signature import PKCS1_v1_5
from httpsig.utils import HttpSigException, HASHES
from abc import ABCMeta, abstractmethod

DEFAULT_HASH_ALGORITHM = "sha256"


class SignAlgorithm(object):
    __metaclass__ = ABCMeta

    @abstractmethod
    def sign(self, private, data):
        raise NotImplementedError()

    @abstractmethod
    def verify(self, public, data, signature):
        raise NotImplementedError()


class PSS(SignAlgorithm):

    def __init__(self, hash_algorithm=DEFAULT_HASH_ALGORITHM, salt_length=None, mgfunc=None):
        if hash_algorithm not in HASHES:
            raise HttpSigException("Unsupported hash algorithm")

        if hash_algorithm != DEFAULT_HASH_ALGORITHM:
            raise HttpSigException(
                "Hash algorithm: {} is deprecated. Please use: {}".format(hash_algorithm, DEFAULT_HASH_ALGORITHM))

        self.hash_algorithm = HASHES[hash_algorithm]
        self.salt_length = salt_length
        self.mgfunc = mgfunc

        if self.salt_length is None:
            self.salt_length = self.hash_algorithm.digest_size

    def _create_pss(self, key):
        try:
            rsa_key = RSA.importKey(key)
            #pss = PKCS1_PSS.new(rsa_key, saltLen=self.salt_length, mgfunc=self.mgfunc)
            pss = PKCS1_v1_5.new(rsa_key)
        except ValueError:
            raise HttpSigException("Invalid key.")
        return pss

    def sign(self, private_key, data):
        if isinstance(data, six.string_types):
            data = data.encode("ascii")

        h = self.hash_algorithm.new()
        h.update(data)

        pss = self._create_pss(private_key)

        return pss.sign(h)

    def verify(self, public_key, data, signature):
        h = self.hash_algorithm.new()
        h.update(data)

        pss = self._create_pss(public_key)

        return pss.verify(h, base64.b64decode(signature))
