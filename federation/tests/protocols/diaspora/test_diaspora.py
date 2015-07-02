from base64 import urlsafe_b64decode
from lxml import etree
import pytest
from federation.exceptions import EncryptedMessageError, NoSenderKeyFoundError

from federation.protocols.diaspora.protocol import DiasporaProtocol


UNENCRYPTED_DOCUMENT = """<?xml version='1.0'?>
            <diaspora xmlns="https://joindiaspora.com/protocol" xmlns:me="http://salmon-protocol.org/ns/magic-env">
                <header>
                    <author_id>bob@example.com</author_id>
                </header>
                <me:env>
                    <me:data type='application/xml'>{data}</me:data>
                    <me:encoding>base64url</me:encoding>
                    <me:alg>RSA-SHA256</me:alg>
                    <me:sig>{signature}</me:sig>
                </me:env>
            </diaspora>
        """

ENCRYPTED_DOCUMENT = """<?xml version='1.0'?>
            <diaspora xmlns="https://joindiaspora.com/protocol" xmlns:me="http://salmon-protocol.org/ns/magic-env">
                <encrypted_header>{encrypted_header}</encrypted_header>
                <content />
            </diaspora>
        """


class MockUser(object):
    key = "foobar"

    def __init__(self, nokey=False):
        if nokey:
            self.key = None


def mock_get_contact_key(contact):
    return "foobar"


def mock_not_found_get_contact_key(contact):
    return None


class TestDiasporaProtocol():

    def test_find_unencrypted_header(self):
        protocol = self.init_protocol()
        protocol.doc = self.get_unencrypted_doc()
        protocol.find_header()
        assert protocol.header is not None
        assert protocol.encrypted is False

    def test_find_encrypted_header(self):
        protocol = self.init_protocol()
        protocol.doc = self.get_encrypted_doc()
        protocol.user = self.get_mock_user()
        protocol.parse_header = self.mock_parse_encrypted_header
        protocol.find_header()
        assert protocol.header is not None
        assert protocol.encrypted is True

    def test_receive_unencrypted_returns_sender_and_content(self):
        protocol = self.init_protocol(contact_key_fetcher=mock_get_contact_key)
        user = self.get_mock_user()
        protocol.get_message_content = self.mock_get_message_content
        sender, content = protocol.receive(UNENCRYPTED_DOCUMENT, user)
        assert sender == "bob@example.com"
        assert content == "<content />"

    def test_receive_raises_on_encrypted_message_and_no_user(self):
        protocol = self.init_protocol()
        with pytest.raises(EncryptedMessageError):
            protocol.receive(ENCRYPTED_DOCUMENT)

    def test_receive_raises_on_encrypted_message_and_no_user_key(self):
        protocol = self.init_protocol()
        user = self.get_mock_user(nokey=True)
        with pytest.raises(EncryptedMessageError):
            protocol.receive(ENCRYPTED_DOCUMENT, user)

    def test_receive_raises_if_sender_key_cannot_be_found(self):
        protocol = self.init_protocol(contact_key_fetcher=mock_not_found_get_contact_key)
        user = self.get_mock_user()
        with pytest.raises(NoSenderKeyFoundError):
            protocol.receive(UNENCRYPTED_DOCUMENT, user)

    def test_get_message_content(self):
        protocol = self.init_protocol()
        protocol.doc = self.get_unencrypted_doc()
        protocol.verify_signature = self.mock_verify_signature
        protocol.sender_key = "foobar"
        protocol.encrypted = False
        body = protocol.get_message_content()
        assert body == urlsafe_b64decode("{data}".encode("ascii"))

    def init_protocol(self, contact_key_fetcher=None):
        return DiasporaProtocol(contact_key_fetcher=contact_key_fetcher)

    def get_unencrypted_doc(self):
        return etree.fromstring(UNENCRYPTED_DOCUMENT)

    def get_encrypted_doc(self):
        return etree.fromstring(ENCRYPTED_DOCUMENT)

    def get_mock_user(self, nokey=False):
        return MockUser(nokey)

    def mock_parse_encrypted_header(self, text, key):
        if text and key:
            return "{encrypted_header}"
        return None

    def mock_get_message_content(self):
        return "<content />"

    def mock_verify_signature(self, contact, payload, sig):
        return True
