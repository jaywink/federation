from unittest.mock import Mock, patch

from lxml import etree
import pytest

from federation.entities.diaspora.entities import DiasporaPost
from federation.entities.diaspora.mappers import get_outbound_entity
from federation.exceptions import NoSenderKeyFoundError, SignatureVerificationError
from federation.protocols.diaspora.protocol import Protocol, identify_request
from federation.tests.fixtures.keys import PUBKEY, get_dummy_private_key
from federation.tests.fixtures.payloads import DIASPORA_PUBLIC_PAYLOAD, DIASPORA_ENCRYPTED_PAYLOAD, \
    DIASPORA_RESHARE_PAYLOAD
from federation.types import RequestType, UserType


class MockUser:
    def __init__(self, nokey=False):
        if nokey:
            self.private_key = None
        else:
            self.private_key = get_dummy_private_key()


def mock_get_contact_key(contact):
    return "foobar"


def mock_not_found_get_contact_key(contact):
    return None


class DiasporaTestBase:
    def init_protocol(self):
        return Protocol()

    def get_unencrypted_doc(self):
        return etree.fromstring(DIASPORA_PUBLIC_PAYLOAD.encode('utf-8'))

    def get_mock_user(self, nokey=False):
        return MockUser(nokey)

    def mock_get_message_content(self):
        return "<content />"


class TestDiasporaProtocol(DiasporaTestBase):
    def test_receive_unencrypted_returns_sender_and_content(self):
        protocol = self.init_protocol()
        user = self.get_mock_user()
        protocol.get_message_content = self.mock_get_message_content
        sender, content = protocol.receive(RequestType(body=DIASPORA_PUBLIC_PAYLOAD), user, mock_get_contact_key,
                                           skip_author_verification=True)
        assert sender == "foobar@example.com"
        assert content == "<content />"

    @patch("federation.protocols.diaspora.protocol.fetch_public_key", autospec=True)
    def test_receive_raises_if_sender_key_cannot_be_found(self, mock_fetch):
        protocol = self.init_protocol()
        user = self.get_mock_user()
        with pytest.raises(NoSenderKeyFoundError):
            protocol.receive(RequestType(body=DIASPORA_PUBLIC_PAYLOAD), user, mock_not_found_get_contact_key)
        assert not mock_fetch.called

    @patch("federation.protocols.diaspora.protocol.fetch_public_key", autospec=True, return_value=None)
    def test_receive_calls_fetch_public_key_if_key_fetcher_not_given(self, mock_fetch):
        protocol = self.init_protocol()
        user = self.get_mock_user()
        with pytest.raises(NoSenderKeyFoundError):
            protocol.receive(RequestType(body=DIASPORA_PUBLIC_PAYLOAD), user)
        mock_fetch.assert_called_once_with("foobar@example.com")

    @patch("federation.protocols.diaspora.protocol.MagicEnvelope", autospec=True)
    @patch("federation.protocols.diaspora.protocol.fetch_public_key", autospec=True, return_value="key")
    def test_receive_creates_and_verifies_magic_envelope_instance(self, mock_fetch, mock_env):
        protocol = self.init_protocol()
        user = self.get_mock_user()
        protocol.receive(RequestType(body=DIASPORA_PUBLIC_PAYLOAD), user)
        mock_env.assert_called_once_with(doc=protocol.doc, public_key="key", verify=True)

    @patch("federation.protocols.diaspora.protocol.fetch_public_key", autospec=True)
    def test_receive_raises_on_signature_verification_failure(self, mock_fetch):
        mock_fetch.return_value = PUBKEY
        protocol = self.init_protocol()
        user = self.get_mock_user()
        with pytest.raises(SignatureVerificationError):
            protocol.receive(RequestType(body=DIASPORA_PUBLIC_PAYLOAD), user)

    def test_get_message_content(self):
        protocol = self.init_protocol()
        protocol.doc = self.get_unencrypted_doc()
        body = protocol.get_message_content()
        assert body == b"<status_message><foo>bar</foo></status_message>"

    def test_identify_payload_with_diaspora_public_payload(self):
        assert identify_request(RequestType(body=DIASPORA_PUBLIC_PAYLOAD)) is True
        assert identify_request(RequestType(body=bytes(DIASPORA_PUBLIC_PAYLOAD, encoding="utf-8"))) is True

    def test_identify_payload_with_diaspora_encrypted_payload(self):
        assert identify_request(RequestType(body=DIASPORA_ENCRYPTED_PAYLOAD)) is True

    def test_identify_payload_with_other_payload(self):
        assert identify_request(RequestType(body="foobar not a diaspora protocol")) is False

    def test_identify_payload_with_reshare(self):
        assert identify_request(RequestType(body=DIASPORA_RESHARE_PAYLOAD)) is True

    @patch("federation.protocols.diaspora.protocol.MagicEnvelope")
    def test_build_send_does_right_calls(self, mock_me):
        mock_render = Mock(return_value="rendered")
        mock_me_instance = Mock(render=mock_render)
        mock_me.return_value = mock_me_instance
        protocol = Protocol()
        entity = DiasporaPost()
        private_key = get_dummy_private_key()
        outbound_entity = get_outbound_entity(entity, private_key)
        data = protocol.build_send(outbound_entity, from_user=UserType(
            private_key=private_key, id="johnny@localhost",
            handle="johnny@localhost",
        ))
        mock_me.assert_called_once_with(
            etree.tostring(entity.to_xml()), private_key=private_key, author_handle="johnny@localhost",
        )
        mock_render.assert_called_once_with()
        assert data == "rendered"

    @patch("federation.protocols.diaspora.protocol.MagicEnvelope")
    @patch("federation.protocols.diaspora.protocol.EncryptedPayload.encrypt", return_value="encrypted")
    def test_build_send_does_right_calls__private_payload(self, mock_encrypt, mock_me):
        mock_render = Mock(return_value="rendered")
        mock_me_instance = Mock(render=mock_render)
        mock_me.return_value = mock_me_instance
        protocol = Protocol()
        entity = DiasporaPost()
        private_key = get_dummy_private_key()
        outbound_entity = get_outbound_entity(entity, private_key)
        data = protocol.build_send(outbound_entity, to_user_key="public key", from_user=UserType(
            private_key=private_key, id="johnny@localhost",
            handle="johnny@localhost",
        ))
        mock_me.assert_called_once_with(
            etree.tostring(entity.to_xml()), private_key=private_key, author_handle="johnny@localhost",
        )
        mock_render.assert_called_once_with()
        mock_encrypt.assert_called_once_with(
            "rendered", "public key",
        )
        assert data == "encrypted"

    @patch("federation.protocols.diaspora.protocol.MagicEnvelope")
    def test_build_send_uses_outbound_doc(self, mock_me):
        protocol = self.init_protocol()
        outbound_doc = etree.fromstring("<xml>foo</xml>")
        entity = Mock(outbound_doc=outbound_doc)
        from_user = UserType(
            id="foobar@domain.tld", private_key=get_dummy_private_key(), handle="foobar@domain.tld",
        )
        protocol.build_send(entity, from_user)
        mock_me.assert_called_once_with(
            b"<xml>foo</xml>", private_key=from_user.private_key, author_handle="foobar@domain.tld",
        )

    @patch("federation.protocols.diaspora.protocol.EncryptedPayload.decrypt")
    def test_get_json_payload_magic_envelope(self, mock_decrypt):
        protocol = Protocol()
        protocol.user = UserType(id="foobar", private_key=get_dummy_private_key())
        protocol.get_json_payload_magic_envelope("payload")
        mock_decrypt.assert_called_once_with(payload="payload", private_key=get_dummy_private_key())

    @patch.object(Protocol, "get_json_payload_magic_envelope", return_value=etree.fromstring("<foo>bar</foo>"))
    def test_store_magic_envelope_doc_json_payload(self, mock_store):
        protocol = Protocol()
        protocol.store_magic_envelope_doc('{"foo": "bar"}')
        mock_store.assert_called_once_with({"foo": "bar"})
        assert protocol.doc.tag == "foo"
        assert protocol.doc.text == "bar"

    def test_store_magic_envelope_doc_xml_payload(self):
        protocol = Protocol()
        protocol.store_magic_envelope_doc("<foo>bar</foo>")
        assert protocol.doc.tag == "foo"
        assert protocol.doc.text == "bar"
