# -*- coding: utf-8 -*-
from base64 import urlsafe_b64decode
from unittest.mock import Mock, patch
from xml.etree.ElementTree import ElementTree

from lxml import etree
import pytest

from federation.exceptions import EncryptedMessageError, NoSenderKeyFoundError, NoHeaderInMessageError
from federation.protocols.diaspora.protocol import Protocol, identify_payload
from federation.tests.factories.entities import DiasporaPostFactory
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


class DiasporaTestBase(object):
    def init_protocol(self):
        return Protocol()

    def get_unencrypted_doc(self):
        return etree.fromstring(UNENCRYPTED_DIASPORA_PAYLOAD)

    def get_encrypted_doc(self):
        return etree.fromstring(ENCRYPTED_DIASPORA_PAYLOAD)

    def get_mock_user(self, nokey=False):
        return MockUser(nokey)

    def mock_parse_encrypted_header(self, text, key):
        return "{encrypted_header}"

    def mock_get_message_content(self):
        return "<content />"


class TestDiasporaProtocol(DiasporaTestBase):
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
        sender, content = protocol.receive(UNENCRYPTED_DIASPORA_PAYLOAD, user, mock_get_contact_key,
                                           skip_author_verification=True)
        assert sender == "bob@example.com"
        assert content == "<content />"

    def test_receive_encrypted_returns_sender_and_content(self):
        protocol = self.init_protocol()
        user = self.get_mock_user()
        protocol.get_message_content = Mock(
            return_value="<content><diaspora_handle>bob@example.com</diaspora_handle></content>"
        )
        protocol.parse_header = Mock(return_value="foobar")
        sender, content = protocol.receive(ENCRYPTED_DIASPORA_PAYLOAD, user, mock_get_contact_key,
                                           skip_author_verification=True)
        assert sender == "bob@example.com"
        assert content == "<content><diaspora_handle>bob@example.com</diaspora_handle></content>"

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

    def test_find_header_raises_if_header_cannot_be_found(self):
        protocol = self.init_protocol()
        protocol.doc = etree.fromstring("<foo>bar</foo>")
        with pytest.raises(NoHeaderInMessageError):
            protocol.find_header()

    def test_get_message_content(self):
        protocol = self.init_protocol()
        protocol.doc = self.get_unencrypted_doc()
        protocol.encrypted = False
        body = protocol.get_message_content()
        assert body == urlsafe_b64decode("{data}".encode("ascii"))

    def test_identify_payload_with_diaspora_payload(self):
        assert identify_payload(UNENCRYPTED_DIASPORA_PAYLOAD) == True

    def test_identify_payload_with_other_payload(self):
        assert identify_payload("foobar not a diaspora protocol") == False

    def test_get_sender_returns_sender_in_header(self):
        protocol = self.init_protocol()
        protocol.doc = self.get_unencrypted_doc()
        protocol.find_header()
        assert protocol.get_sender() == "bob@example.com"

    def test_get_sender_returns_sender_in_content(self):
        protocol = self.init_protocol()
        protocol.header = ElementTree()
        protocol.content = "<content><diaspora_handle>bob@example.com</diaspora_handle></content>"
        assert protocol.get_sender() == "bob@example.com"
        protocol.content = "<content><sender_handle>bob@example.com</sender_handle></content>"
        assert protocol.get_sender() == "bob@example.com"

    def test_get_sender_returns_none_if_no_sender_found(self):
        protocol = self.init_protocol()
        protocol.header = ElementTree()
        protocol.content = "<content><handle>bob@example.com</handle></content>"
        assert protocol.get_sender() == None

    @patch.object(Protocol, "init_message")
    @patch.object(Protocol, "create_salmon_envelope")
    def test_build_send(self, mock_create_salmon, mock_init_message):
        mock_create_salmon.return_value = "xmldata"
        protocol = self.init_protocol()
        mock_entity_xml = Mock()
        entity = Mock(to_xml=Mock(return_value=mock_entity_xml))
        from_user = Mock(handle="foobar", private_key="barfoo")
        data = protocol.build_send(from_user, Mock(), entity)
        mock_init_message.assert_called_once_with(mock_entity_xml, from_user.handle, from_user.private_key)
        assert data == {"xml": "xmldata"}
