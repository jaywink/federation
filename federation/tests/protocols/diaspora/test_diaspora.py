from base64 import urlsafe_b64decode
from lxml import etree
import pytest

from federation.exceptions import EncryptedMessageError, NoSenderKeyFoundError
from federation.protocols.diaspora.protocol import Protocol, identify_payload
from federation.tests.fixtures.payloads import ENCRYPTED_DIASPORA_PAYLOAD, UNENCRYPTED_DIASPORA_PAYLOAD


class MockUser(object):
    key = "foobar"

    def __init__(self, nokey=False):
        if nokey:
            self.key = None


def mock_get_contact_key(contact):
    return "foobar"


def mock_not_found_get_contact_key(contact):
    return None


class TestDiasporaProtocol(object):

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
        protocol = self.init_protocol()
        user = self.get_mock_user()
        protocol.get_message_content = self.mock_get_message_content
        sender, content = protocol.receive(UNENCRYPTED_DIASPORA_PAYLOAD, user, mock_get_contact_key)
        assert sender == "bob@example.com"
        assert content == "<content />"

    def test_receive_raises_on_encrypted_message_and_no_user(self):
        protocol = self.init_protocol()
        with pytest.raises(EncryptedMessageError):
            protocol.receive(ENCRYPTED_DIASPORA_PAYLOAD)

    def test_receive_raises_on_encrypted_message_and_no_user_key(self):
        protocol = self.init_protocol()
        user = self.get_mock_user(nokey=True)
        with pytest.raises(EncryptedMessageError):
            protocol.receive(ENCRYPTED_DIASPORA_PAYLOAD, user)

    def test_receive_raises_if_sender_key_cannot_be_found(self):
        protocol = self.init_protocol()
        user = self.get_mock_user()
        with pytest.raises(NoSenderKeyFoundError):
            protocol.receive(UNENCRYPTED_DIASPORA_PAYLOAD, user, mock_not_found_get_contact_key)

    def test_get_message_content(self):
        protocol = self.init_protocol()
        protocol.doc = self.get_unencrypted_doc()
        protocol.verify_signature = self.mock_verify_signature
        protocol.skip_author_verification = False
        protocol.sender_key = "foobar"
        protocol.encrypted = False
        body = protocol.get_message_content()
        assert body == urlsafe_b64decode("{data}".encode("ascii"))

    def test_identify_payload_with_diaspora_payload(self):
        assert identify_payload(UNENCRYPTED_DIASPORA_PAYLOAD) == True

    def test_identify_payload_with_other_payload(self):
        assert identify_payload("foobar not a diaspora protocol") == False

    def init_protocol(self):
        return Protocol()

    def get_unencrypted_doc(self):
        return etree.fromstring(UNENCRYPTED_DIASPORA_PAYLOAD)

    def get_encrypted_doc(self):
        return etree.fromstring(ENCRYPTED_DIASPORA_PAYLOAD)

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
