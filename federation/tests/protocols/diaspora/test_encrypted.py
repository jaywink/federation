from unittest.mock import patch, Mock

from Crypto.Cipher import AES

from federation.protocols.diaspora.encrypted import pkcs7_unpad, EncryptedPayload


def test_pkcs7_unpad():
    assert pkcs7_unpad(b"foobar\x02\x02") == b"foobar"
    assert pkcs7_unpad("foobar\x02\x02") == "foobar"


class TestEncryptedPayload:
    @patch("federation.protocols.diaspora.encrypted.PKCS1_v1_5.new")
    @patch("federation.protocols.diaspora.encrypted.AES.new")
    @patch("federation.protocols.diaspora.encrypted.pkcs7_unpad", side_effect=lambda x: x)
    @patch("federation.protocols.diaspora.encrypted.b64decode", side_effect=lambda x: x)
    def test_decrypt(self, mock_decode, mock_unpad, mock_aes, mock_pkcs1):
        mock_decrypt = Mock(return_value=b'{"iv": "foo", "key": "bar"}')
        mock_pkcs1.return_value = Mock(decrypt=mock_decrypt)
        mock_encrypter = Mock(return_value="<foo>bar</foo>")
        mock_aes.return_value = Mock(decrypt=mock_encrypter)
        doc = EncryptedPayload.decrypt(
            {"aes_key": '{"iv": "foo", "key": "bar"}', "encrypted_magic_envelope": "magically encrypted"},
            "private_key",
        )
        mock_pkcs1.assert_called_once_with("private_key")
        mock_decrypt.assert_called_once_with('{"iv": "foo", "key": "bar"}', sentinel=None)
        assert mock_decode.call_count == 4
        mock_aes.assert_called_once_with("bar", AES.MODE_CBC, "foo")
        mock_encrypter.assert_called_once_with("magically encrypted")
        assert doc.tag == "foo"
        assert doc.text == "bar"
