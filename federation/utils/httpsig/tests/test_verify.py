#!/usr/bin/env python
import sys
import os
import unittest

from httpsig.sign import HeaderSigner, Signer
from httpsig.sign_algorithms import PSS
from httpsig.verify import HeaderVerifier, Verifier

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class BaseTestCase(unittest.TestCase):

    def _parse_auth(self, auth):
        """Basic Authorization header parsing."""
        # split 'Signature kvpairs'
        s, param_str = auth.split(' ', 1)
        self.assertEqual(s, 'Signature')
        # split k1="v1",k2="v2",...
        param_list = param_str.split(',')
        # convert into [(k1,"v1"), (k2, "v2"), ...]
        param_pairs = [p.split('=', 1) for p in param_list]
        # convert into {k1:v1, k2:v2, ...}
        param_dict = {k: v.strip('"') for k, v in param_pairs}
        return param_dict


class TestVerifyHMACSHA1(BaseTestCase):
    test_method = 'POST'
    test_path = '/foo?param=value&pet=dog'
    header_host = 'example.com'
    header_date = 'Thu, 05 Jan 2014 21:31:40 GMT'
    header_content_type = 'application/json'
    header_digest = 'SHA-256=X48E9qOokqqrvdts8nOJRJN3OWDUoyWxBf7kbu9DBPE='
    header_content_length = '18'
    sign_header = 'authorization'

    def setUp(self):
        secret = b"something special goes here"

        self.keyId = "Test"
        self.algorithm = "hmac-sha1"
        self.sign_secret = secret
        self.verify_secret = secret
        self.sign_algorithm = None

    def test_basic_sign(self):
        signer = Signer(secret=self.sign_secret, algorithm=self.algorithm, sign_algorithm=self.sign_algorithm)
        verifier = Verifier(
            secret=self.verify_secret, algorithm=self.algorithm, sign_algorithm=self.sign_algorithm)

        GOOD = b"this is a test"
        BAD = b"this is not the signature you were looking for..."

        # generate signed string
        signature = signer.sign(GOOD)
        self.assertTrue(verifier._verify(data=GOOD, signature=signature))
        self.assertFalse(verifier._verify(data=BAD, signature=signature))

    def test_default(self):
        unsigned = {
            'Date': self.header_date
        }

        hs = HeaderSigner(
            key_id="Test", secret=self.sign_secret, algorithm=self.algorithm,
            sign_header=self.sign_header, sign_algorithm=self.sign_algorithm)
        signed = hs.sign(unsigned)
        hv = HeaderVerifier(
            headers=signed, secret=self.verify_secret, sign_header=self.sign_header, sign_algorithm=self.sign_algorithm)
        self.assertTrue(hv.verify())

    def test_signed_headers(self):
        HOST = self.header_host
        METHOD = self.test_method
        PATH = self.test_path
        hs = HeaderSigner(
            key_id="Test",
            secret=self.sign_secret,
            algorithm=self.algorithm,
            sign_header=self.sign_header,
            headers=[
                '(request-target)',
                'host',
                'date',
                'content-type',
                'digest',
                'content-length'
            ],
            sign_algorithm=self.sign_algorithm)
        unsigned = {
            'Host': HOST,
            'Date': self.header_date,
            'Content-Type': self.header_content_type,
            'Digest': self.header_digest,
            'Content-Length': self.header_content_length,
        }
        signed = hs.sign(unsigned, method=METHOD, path=PATH)

        hv = HeaderVerifier(
            headers=signed, secret=self.verify_secret,
            host=HOST, method=METHOD, path=PATH,
            sign_header=self.sign_header, sign_algorithm=self.sign_algorithm)
        self.assertTrue(hv.verify())

    def test_incorrect_headers(self):
        HOST = self.header_host
        METHOD = self.test_method
        PATH = self.test_path
        hs = HeaderSigner(secret=self.sign_secret,
                          key_id="Test",
                          algorithm=self.algorithm,
                          sign_header=self.sign_header,
                          headers=[
                              '(request-target)',
                              'host',
                              'date',
                              'content-type',
                              'digest',
                              'content-length'],
                          sign_algorithm=self.sign_algorithm)
        unsigned = {
            'Host': HOST,
            'Date': self.header_date,
            'Content-Type': self.header_content_type,
            'Digest': self.header_digest,
            'Content-Length': self.header_content_length,
        }
        signed = hs.sign(unsigned, method=METHOD, path=PATH)

        hv = HeaderVerifier(headers=signed, secret=self.verify_secret,
                            required_headers=["some-other-header"],
                            host=HOST, method=METHOD, path=PATH,
                            sign_header=self.sign_header, sign_algorithm=self.sign_algorithm)
        with self.assertRaises(ValueError) as e:
            hv.verify()
        self.assertEqual(str(e.exception), 'some-other-header is a required header(s)')

    def test_extra_auth_headers(self):
        HOST = "example.com"
        METHOD = "POST"
        PATH = '/foo?param=value&pet=dog'
        hs = HeaderSigner(
            key_id="Test",
            secret=self.sign_secret,
            sign_header=self.sign_header,
            algorithm=self.algorithm, headers=[
                '(request-target)',
                'host',
                'date',
                'content-type',
                'digest',
                'content-length'
            ],
            sign_algorithm=self.sign_algorithm)
        unsigned = {
            'Host': HOST,
            'Date': self.header_date,
            'Content-Type': self.header_content_type,
            'Digest': self.header_digest,
            'Content-Length': self.header_content_length,
        }
        signed = hs.sign(unsigned, method=METHOD, path=PATH)
        hv = HeaderVerifier(
            headers=signed,
            secret=self.verify_secret,
            method=METHOD,
            path=PATH,
            sign_header=self.sign_header,
            required_headers=['date', '(request-target)'],
            sign_algorithm=self.sign_algorithm)
        self.assertTrue(hv.verify())

    def test_empty_secret(self):
        with self.assertRaises(ValueError) as e:
            HeaderVerifier(secret='', headers={})
        self.assertEqual(str(e.exception), 'secret cant be empty')

    def test_none_secret(self):
        with self.assertRaises(ValueError) as e:
            HeaderVerifier(secret=None, headers={})
        self.assertEqual(str(e.exception), 'secret cant be empty')

    def test_huge_secret(self):
        with self.assertRaises(ValueError) as e:
            HeaderVerifier(secret='x' * 1000000, headers={})
        self.assertEqual(str(e.exception), 'secret cant be larger than 100000 chars')


class TestVerifyHMACSHA256(TestVerifyHMACSHA1):

    def setUp(self):
        super(TestVerifyHMACSHA256, self).setUp()
        self.algorithm = "hmac-sha256"


class TestVerifyHMACSHA512(TestVerifyHMACSHA1):

    def setUp(self):
        super(TestVerifyHMACSHA512, self).setUp()
        self.algorithm = "hmac-sha512"


class TestVerifyRSASHA1(TestVerifyHMACSHA1):

    def setUp(self):
        private_key_path = os.path.join(
            os.path.dirname(__file__),
            'rsa_private_1024.pem')
        with open(private_key_path, 'rb') as f:
            private_key = f.read()

        public_key_path = os.path.join(
            os.path.dirname(__file__),
            'rsa_public_1024.pem')
        with open(public_key_path, 'rb') as f:
            public_key = f.read()

        self.keyId = "Test"
        self.algorithm = "rsa-sha1"
        self.sign_secret = private_key
        self.verify_secret = public_key
        self.sign_algorithm = None


class TestVerifyRSASHA256(TestVerifyRSASHA1):

    def setUp(self):
        super(TestVerifyRSASHA256, self).setUp()
        self.algorithm = "rsa-sha256"


class TestVerifyRSASHA512(TestVerifyRSASHA1):

    def setUp(self):
        super(TestVerifyRSASHA512, self).setUp()
        self.algorithm = "rsa-sha512"


class TestVerifyRSASHA512ChangeHeader(TestVerifyRSASHA1):
    sign_header = 'Signature'


class TestVerifyHS2019PSS(TestVerifyHMACSHA1):

    def setUp(self):
        private_key_path = os.path.join(os.path.dirname(__file__), 'rsa_private_2048.pem')
        with open(private_key_path, 'rb') as f:
            private_key = f.read()

        public_key_path = os.path.join(os.path.dirname(__file__), 'rsa_public_2048.pem')
        with open(public_key_path, 'rb') as f:
            public_key = f.read()

        self.keyId = "Test"
        self.algorithm = "hs2019"
        self.sign_secret = private_key
        self.verify_secret = public_key
        self.sign_algorithm = PSS(salt_length=0)

    def test_algorithm_mismatch(self):
        unsigned = {
            'Date': self.header_date
        }

        hs = HeaderSigner(
            key_id="Test", secret=self.sign_secret, algorithm=self.algorithm,
            sign_header=self.sign_header, sign_algorithm=self.sign_algorithm)
        signed = hs.sign(unsigned)

        hv = HeaderVerifier(
            headers=signed, secret=self.verify_secret, sign_header=self.sign_header, algorithm="rsa-sha256", sign_algorithm=self.sign_algorithm)
        self.assertFalse(hv.verify())

    def test_correct_derived_algorithm(self):
        unsigned = {
            'Date': self.header_date
        }

        hs = HeaderSigner(
            key_id="Test", secret=self.sign_secret, algorithm=self.algorithm,
            sign_header=self.sign_header, sign_algorithm=self.sign_algorithm)
        signed = hs.sign(unsigned)

        hv = HeaderVerifier(
            headers=signed, secret=self.verify_secret, sign_header=self.sign_header, algorithm="hs2019", sign_algorithm=self.sign_algorithm)
        self.assertTrue(hv.verify())


class TestSignAndVerify(unittest.TestCase):
    header_date = 'Thu, 05 Jan 2014 21:31:40 GMT'
    sign_header = 'authorization'

    def setUp(self):
        with open(os.path.join(os.path.dirname(__file__), 'rsa_private_1024.pem'), 'rb') as f:
            self.private_key = f.read()

        with open(os.path.join(os.path.dirname(__file__), 'rsa_public_1024.pem'), 'rb') as f:
            self.public_key = f.read()

        with open(os.path.join(os.path.dirname(__file__), 'rsa_private_2048.pem'), 'rb') as f:
            self.other_private_key = f.read()

        with open(os.path.join(os.path.dirname(__file__), 'rsa_public_2048.pem'), 'rb') as f:
            self.other_public_key = f.read()

    def test_default(self):
        unsigned = {
            'Date': self.header_date
        }

        hs = HeaderSigner(
            key_id="Test", secret=self.private_key, algorithm='rsa-sha1',
            sign_header=self.sign_header)
        signed = hs.sign(unsigned)
        hv = HeaderVerifier(
            headers=signed, secret=self.public_key, sign_header=self.sign_header)
        self.assertTrue(hv.verify())

    def test_other_default(self):
        unsigned = {
            'Date': self.header_date
        }

        hs = HeaderSigner(
            key_id="Test", secret=self.other_private_key, algorithm='rsa-sha256',
            sign_header=self.sign_header)
        signed = hs.sign(unsigned)
        hv = HeaderVerifier(
            headers=signed, secret=self.other_public_key, sign_header=self.sign_header)
        self.assertTrue(hv.verify())

    def test_mix_default_1_256(self):
        unsigned = {
            'Date': self.header_date
        }

        hs = HeaderSigner(
            key_id="Test", secret=self.private_key, algorithm='rsa-sha1',
            sign_header=self.sign_header)
        signed = hs.sign(unsigned)
        hv = HeaderVerifier(
            headers=signed, secret=self.other_public_key, sign_header=self.sign_header)
        self.assertFalse(hv.verify())

    def test_mix_default_256_1(self):
        unsigned = {
            'Date': self.header_date
        }

        hs = HeaderSigner(
            key_id="Test", secret=self.other_private_key, algorithm='rsa-sha256',
            sign_header=self.sign_header)
        signed = hs.sign(unsigned)
        hv = HeaderVerifier(
            headers=signed, secret=self.public_key, sign_header=self.sign_header)
        self.assertFalse(hv.verify())
