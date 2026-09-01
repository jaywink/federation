#!/usr/bin/env python
import sys
import os

import unittest

import pytest

import httpsig.sign as sign
from httpsig.sign_algorithms import PSS
from httpsig.utils import parse_authorization_header, HttpSigException

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

sign.DEFAULT_ALGORITHM = "hs2019"


class TestSign(unittest.TestCase):
    test_method = 'POST'
    test_path = '/foo?param=value&pet=dog'
    header_host = 'example.com'
    header_date = 'Thu, 05 Jan 2014 21:31:40 GMT'
    header_content_type = 'application/json'
    header_digest = 'SHA-256=X48E9qOokqqrvdts8nOJRJN3OWDUoyWxBf7kbu9DBPE='
    header_content_length = '18'

    def setUp(self):
        self.key_path_2048 = os.path.join(
            os.path.dirname(__file__), 'rsa_private_2048.pem')
        with open(self.key_path_2048, 'rb') as f:
            self.key_2048 = f.read()

        self.key_path_1024 = os.path.join(
            os.path.dirname(__file__), 'rsa_private_1024.pem')
        with open(self.key_path_1024, 'rb') as f:
            self.key_1024 = f.read()

    def test_default(self):
        hs = sign.HeaderSigner(key_id='Test', secret=self.key_2048, sign_algorithm=PSS(hash_algorithm="sha512", salt_length=0))
        unsigned = {
            'Date': self.header_date
        }
        signed = hs.sign(unsigned)
        self.assertIn('Date', signed)
        self.assertEqual(unsigned['Date'], signed['Date'])
        self.assertIn('Authorization', signed)
        auth = parse_authorization_header(signed['authorization'])
        params = auth[1]
        self.assertIn('keyId', params)
        self.assertIn('algorithm', params)
        self.assertIn('signature', params)
        self.assertEqual(params['keyId'], 'Test')
        self.assertEqual(params['algorithm'], 'hs2019')
        self.assertEqual(params['signature'], 'T8+Cj3Zp2cBDm2r8/loPgfHUSSFXXyZJNxxbNx1NvKVz/r5T4z6pVxhl9rqk8WfYHMdlh2aT5hCrYKvhs88Jy0DDmeUP4nELWRsO1BF0oAqHfcrbEikZQL7jA6z0guVaLr0S5QRGmd1K5HUEkP/vYEOns+FRL+JrFG4dNJNESvG5iyKUoaXfoZCFdqtzLlIteEAL7dW/kaX/dE116wfpbem1eCABuGopRhuFtjqLKVjuUVwyP/zSYTqd9j+gDhinkAifTJPxbGMh0b5LZdNCqw5irT9NkTcTFRXDp8ioX8r805Z9QhjT7H+rSo350U2LsAFoQ9ttryPBOoMPCiQTlw==')  # noqa: E501

    def test_other_default(self):
        hs = sign.HeaderSigner(key_id='Test', secret=self.key_1024, sign_algorithm=PSS(hash_algorithm="sha512", salt_length=0))
        unsigned = {
            'Date': self.header_date
        }
        signed = hs.sign(unsigned)
        self.assertIn('Date', signed)
        self.assertEqual(unsigned['Date'], signed['Date'])
        self.assertIn('Authorization', signed)
        auth = parse_authorization_header(signed['authorization'])
        params = auth[1]
        self.assertIn('keyId', params)
        self.assertIn('algorithm', params)
        self.assertIn('signature', params)
        self.assertEqual(params['keyId'], 'Test')
        self.assertEqual(params['algorithm'], 'hs2019')
        self.assertEqual(params['signature'],
                         'Gw8FOaXNxqwJHXwJ30OKiMFpK5zP916CFtzK7/biKi9NppjGAlpUfFKqp5kK+bFRyXxqUzQ1x5cbSeFzRWnqodNNO60ApYbOVD7ePqJfZ3DJFAxYOMzoECzc+lyVskSHKC0Ue8aYiV66gXTuY7hrEIqUsK3To/DhSNgO8csdzwg=')

    def test_basic(self):
        hs = sign.HeaderSigner(key_id='Test', secret=self.key_2048, sign_algorithm=PSS(salt_length=0), headers=[
            '(request-target)',
            'host',
            'date',
        ])
        unsigned = {
            'Host': self.header_host,
            'Date': self.header_date,
        }
        signed = hs.sign(
            unsigned, method=self.test_method, path=self.test_path)

        self.assertIn('Date', signed)
        self.assertEqual(unsigned['Date'], signed['Date'])
        self.assertIn('Authorization', signed)
        auth = parse_authorization_header(signed['authorization'])
        params = auth[1]
        self.assertIn('keyId', params)
        self.assertIn('algorithm', params)
        self.assertIn('signature', params)
        self.assertEqual(params['keyId'], 'Test')
        self.assertEqual(params['algorithm'], 'hs2019')
        self.assertEqual(
            params['headers'], '(request-target) host date')
        self.assertEqual(params['signature'], 'KkF4oeOJJH9TaYjQdaU634G7AVmM5Bf3fnfJCBZ7G0H5puW5XlQTpduA+TgouKOJhbv4aRRpunPzCHUxUjEvrR3TSALqW1EOsBwCVIusE9CnrhL7vUOvciIDai/jI15RsfR9+XyTmOSFbsI07E8mmywr3nLeWX6AAFDMO2vWc21zZxrSc13vFfAkVvFhXLxO4g0bBm6Z4m5/9ytWtdE0Gf3St2kY8aZTedllRCS8cMx8GVAIw/qYGeIlGKUCZKxrFxnviN7gfxixwova6lcxpppIo+WXxEiwMJfSQBlx0WGn3A3twCv6TsIxPOVUEW4jcogDh+jGFf1aGdVyHquTRQ==')  # noqa: E501

    def test_all(self):
        hs = sign.HeaderSigner(key_id='Test', secret=self.key_2048, sign_algorithm=PSS("sha512", salt_length=0),  headers=[
            '(request-target)',
            'host',
            'date',
            'content-type',
            'digest',
            'content-length'
        ])
        unsigned = {
            'Host': self.header_host,
            'Date': self.header_date,
            'Content-Type': self.header_content_type,
            'Digest': self.header_digest,
            'Content-Length': self.header_content_length,
        }
        signed = hs.sign(
            unsigned, method=self.test_method, path=self.test_path)

        self.assertIn('Date', signed)
        self.assertEqual(unsigned['Date'], signed['Date'])
        self.assertIn('Authorization', signed)
        auth = parse_authorization_header(signed['authorization'])
        params = auth[1]
        self.assertIn('keyId', params)
        self.assertIn('algorithm', params)
        self.assertIn('signature', params)
        self.assertEqual(params['keyId'], 'Test')
        self.assertEqual(params['algorithm'], 'hs2019')
        self.assertEqual(
            params['headers'],
            '(request-target) host date content-type digest content-length')
        self.assertEqual(params['signature'], 'bxWyLDB/Tuhzxd/tWG2g60l3Goyk9XJZzj2ouNKizZuZoe1Ngj+19N11bhK7FABHJ7lSzH5g6fp5LkN894ivIv6N29L2sPssuAkqgzNXyvYkp4KWOr5j7sVpApmRH7gf7THljcXosmrYk5gdBTspixpJJJ5LGkkPKCRAFurmi/LqopSH6cJbLJNIccTu2dTMGEeDOqqNterVmfonpZyPeBsEEwoeOo6d8zgHzB/1Xxk7dfELFbA1c0LE5kZbwEIEFPmS01YFz6EJW7Aj8kzvzwQRyvgDobi25niGOy/D7JVHvtDjBIaJedFuFJSb8rZ2DGryBQ6NwchMp3f2MUoTGg==')  # noqa: E501

    def test_default_deprecated_256(self):
        hs = sign.HeaderSigner(key_id='Test', secret=self.key_1024, algorithm="rsa-sha256")
        unsigned = {
            'Date': self.header_date
        }
        signed = hs.sign(unsigned)
        self.assertIn('Date', signed)
        self.assertEqual(unsigned['Date'], signed['Date'])
        self.assertIn('Authorization', signed)
        auth = parse_authorization_header(signed['authorization'])
        params = auth[1]
        self.assertIn('keyId', params)
        self.assertIn('algorithm', params)
        self.assertIn('signature', params)
        self.assertEqual(params['keyId'], 'Test')
        self.assertEqual(params['algorithm'], 'rsa-sha256')
        self.assertEqual(params['signature'], 'jKyvPcxB4JbmYY4mByyBY7cZfNl4OW9HpFQlG7N4YcJPteKTu4MWCLyk+gIr0wDgqtLWf9NLpMAMimdfsH7FSWGfbMFSrsVTHNTk0rK3usrfFnti1dxsM4jl0kYJCKTGI/UWkqiaxwNiKqGcdlEDrTcUhhsFsOIo8VhddmZTZ8w=')  # noqa: E501

    def test_unsupported_hash_algorithm(self):
        with pytest.raises(HttpSigException) as e:
            sign.HeaderSigner(key_id='Test', secret=self.key_2048, sign_algorithm=PSS("sha123", salt_length=0))
        self.assertEqual(str(e.value), "Unsupported hash algorithm")

    def test_deprecated_hash_algorithm(self):
        with pytest.raises(HttpSigException) as e:
            sign.HeaderSigner(key_id='Test', secret=self.key_2048, sign_algorithm=PSS("sha256", salt_length=0))
        self.assertEqual(str(e.value), "Hash algorithm: sha256 is deprecated. Please use: sha512")

    def test_empty_secret(self):
        with self.assertRaises(ValueError) as e:
            sign.HeaderSigner(key_id='Test', secret='', headers=[
                '(request-target)',
                'host',
                'date',
                'content-type',
                'digest',
                'content-length'
            ])
        self.assertEqual(str(e.exception), "secret can't be empty")

    def test_none_secret(self):
        with self.assertRaises(ValueError) as e:
            sign.HeaderSigner(key_id='Test', secret=None, headers=[
                '(request-target)',
                'host',
                'date',
                'content-type',
                'digest',
                'content-length'
            ])
        self.assertEqual(str(e.exception), "secret can't be empty")

    def test_huge_secret(self):
        with self.assertRaises(ValueError) as e:
            sign.HeaderSigner(key_id='Test', secret='x' * 1000000, headers=[
                '(request-target)',
                'host',
                'date',
                'content-type',
                'digest',
                'content-length'
            ])
        self.assertEqual(str(e.exception), "secret cant be larger than 100000 chars")

    def test_empty_key_id(self):
        with self.assertRaises(ValueError) as e:
            sign.HeaderSigner(key_id='', secret=self.key_2048, headers=[
                '(request-target)',
                'host',
                'date',
                'content-type',
                'digest',
                'content-length'
            ])
        self.assertEqual(str(e.exception), "key_id can't be empty")

    def test_none_key_id(self):
        with self.assertRaises(ValueError) as e:
            sign.HeaderSigner(key_id=None, secret=self.key_2048, headers=[
                '(request-target)',
                'host',
                'date',
                'content-type',
                'digest',
                'content-length'
            ])
        self.assertEqual(str(e.exception), "key_id can't be empty")

    def test_huge_key_id(self):
        with self.assertRaises(ValueError) as e:
            sign.HeaderSigner(key_id='x' * 1000000, secret=self.key_2048, headers=[
                '(request-target)',
                'host',
                'date',
                'content-type',
                'digest',
                'content-length'
            ])
        self.assertEqual(str(e.exception), "key_id cant be larger than 100000 chars")

    def test_empty_method(self):
        hs = sign.HeaderSigner(key_id='Test', secret=self.key_2048, sign_algorithm=PSS("sha512", salt_length=0), headers=[
            '(request-target)',
            'host',
            'date',
            'content-type',
            'digest',
            'content-length'
        ])
        unsigned = {
            'Host': self.header_host,
            'Date': self.header_date,
            'Content-Type': self.header_content_type,
            'Digest': self.header_digest,
            'Content-Length': self.header_content_length,
        }

        with self.assertRaises(ValueError) as e:
            hs.sign(unsigned, method='', path=self.test_path)
        self.assertEqual(str(e.exception), 'method and path arguments required when using "(request-target)"')

    def test_none_method(self):
        hs = sign.HeaderSigner(key_id='Test', secret=self.key_2048, sign_algorithm=PSS("sha512", salt_length=0), headers=[
            '(request-target)',
            'host',
            'date',
            'content-type',
            'digest',
            'content-length'
        ])
        unsigned = {
            'Host': self.header_host,
            'Date': self.header_date,
            'Content-Type': self.header_content_type,
            'Digest': self.header_digest,
            'Content-Length': self.header_content_length,
        }

        with self.assertRaises(ValueError) as e:
            hs.sign(unsigned, method=None, path=self.test_path)
        self.assertEqual(str(e.exception), 'method and path arguments required when using "(request-target)"')

    def test_empty_path(self):
        hs = sign.HeaderSigner(key_id='Test', secret=self.key_2048, sign_algorithm=PSS("sha512", salt_length=0), headers=[
            '(request-target)',
            'host',
            'date',
            'content-type',
            'digest',
            'content-length'
        ])
        unsigned = {
            'Host': self.header_host,
            'Date': self.header_date,
            'Content-Type': self.header_content_type,
            'Digest': self.header_digest,
            'Content-Length': self.header_content_length,
        }

        with self.assertRaises(ValueError) as e:
            hs.sign(unsigned, method=self.test_method, path='')
        self.assertEqual(str(e.exception), 'method and path arguments required when using "(request-target)"')

    def test_none_path(self):
        hs = sign.HeaderSigner(key_id='Test', secret=self.key_2048, sign_algorithm=PSS("sha512", salt_length=0), headers=[
            '(request-target)',
            'host',
            'date',
            'content-type',
            'digest',
            'content-length'
        ])
        unsigned = {
            'Host': self.header_host,
            'Date': self.header_date,
            'Content-Type': self.header_content_type,
            'Digest': self.header_digest,
            'Content-Length': self.header_content_length,
        }

        with self.assertRaises(ValueError) as e:
            hs.sign(unsigned, method=self.test_method, path=None)
        self.assertEqual(str(e.exception), 'method and path arguments required when using "(request-target)"')

    def test_missing_header_host(self):
        hs = sign.HeaderSigner(key_id='Test', secret=self.key_2048, sign_algorithm=PSS("sha512", salt_length=0), headers=[
            '(request-target)',
            'host',
            'date',
            'content-type',
            'digest',
            'content-length'
        ])
        unsigned = {
            'Date': self.header_date,
            'Content-Type': self.header_content_type,
            'Digest': self.header_digest,
            'Content-Length': self.header_content_length,
        }

        with self.assertRaises(ValueError) as e:
            hs.sign(unsigned, method=self.test_method, path=self.test_path)
        self.assertEqual(str(e.exception), 'missing required header "host"')

    def test_missing_header_date(self):
        hs = sign.HeaderSigner(key_id='Test', secret=self.key_2048, sign_algorithm=PSS("sha512", salt_length=0), headers=[
            '(request-target)',
            'host',
            'date',
            'content-type',
            'digest',
            'content-length'
        ])
        unsigned = {
            'Host': self.header_host,
            'Content-Type': self.header_content_type,
            'Digest': self.header_digest,
            'Content-Length': self.header_content_length,
        }

        with self.assertRaises(ValueError) as e:
            hs.sign(unsigned, method=self.test_method, path=self.test_path)
        self.assertEqual(str(e.exception), 'missing required header "date"')

    def test_missing_header_digest(self):
        hs = sign.HeaderSigner(key_id='Test', secret=self.key_2048, sign_algorithm=PSS("sha512", salt_length=0), headers=[
            '(request-target)',
            'host',
            'date',
            'content-type',
            'digest',
            'content-length'
        ])
        unsigned = {
            'Host': self.header_host,
            'Date': self.header_date,
            'Content-Type': self.header_content_type,
            'Content-Length': self.header_content_length,
        }

        with self.assertRaises(ValueError) as e:
            hs.sign(unsigned, method=self.test_method, path=self.test_path)
        self.assertEqual(str(e.exception), 'missing required header "digest"')
