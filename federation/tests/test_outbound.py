from unittest.mock import Mock, patch

from Crypto.PublicKey import RSA

from federation.entities.diaspora.entities import DiasporaPost, DiasporaComment
from federation.outbound import handle_create_payload, handle_send
from federation.tests.fixtures.keys import get_dummy_private_key


class TestHandleCreatePayloadBuildsAPayload:
    @patch("federation.outbound.Protocol")
    def test_handle_create_payload_builds_an_xml(self, mock_protocol_class):
        mock_protocol = Mock()
        mock_protocol_class.return_value = mock_protocol
        author_user = Mock()
        entity = DiasporaPost()
        handle_create_payload(entity, author_user)
        mock_protocol.build_send.assert_called_once_with(entity=entity, from_user=author_user, to_user_key=None)

    @patch("federation.outbound.get_outbound_entity")
    def test_handle_create_payload_calls_get_outbound_entity(self, mock_get_outbound_entity):
        mock_get_outbound_entity.return_value = DiasporaPost()
        author_user = Mock(private_key=RSA.generate(2048), id="diaspora://foobar@domain.tld/profile/")
        entity = DiasporaPost()
        handle_create_payload(entity, author_user)
        mock_get_outbound_entity.assert_called_once_with(entity, author_user.private_key)

    @patch("federation.outbound.get_outbound_entity")
    def test_handle_create_payload_calls_get_outbound_entity_with_author_user(self, mock_get_outbound_entity):
        mock_get_outbound_entity.return_value = DiasporaPost()
        author_user = Mock(private_key=RSA.generate(2048), id="diaspora://foobar@domain.tld/profile/")
        entity = DiasporaPost()
        handle_create_payload(entity, author_user)
        mock_get_outbound_entity.assert_called_once_with(entity, author_user.private_key)

    @patch("federation.outbound.get_outbound_entity")
    def test_handle_create_payload_calls_sign_with_parent(self, mock_get_outbound_entity):
        comment = DiasporaComment()
        mock_get_outbound_entity.return_value = comment
        author_user = Mock(private_key=RSA.generate(2048), id="diaspora://foobar@domain.tld/profile/")
        parent_user = Mock(private_key=RSA.generate(2048), id="diaspora://parent@domain.tld/profile/")
        entity = DiasporaComment()
        with patch.object(comment, "sign_with_parent") as mock_sign:
            handle_create_payload(entity, author_user, parent_user=parent_user)
            mock_sign.assert_called_once_with(parent_user.private_key)


@patch("federation.outbound.send_document")
class TestHandleSend:
    def test_calls_handle_create_payload(self, mock_send, diasporapost):
        key = get_dummy_private_key()
        recipients = [
            ("diaspora://foo@127.0.0.1/profile/xyz", key.publickey()),
            ("diaspora://foo@localhost/profile/abc", None),
            "diaspora://foo@example.net/profile/zzz",
            "diaspora://qwer@example.net/profile/qwerty",  # Same host twice to ensure one delivery only per host
                                                           # for public payloads
        ]
        mock_author = Mock(private_key=key, id="diaspora://foo@example.com/profile/")
        handle_send(diasporapost, mock_author, recipients)

        # Ensure first call is a private payload
        args, kwargs = mock_send.call_args_list[0]
        assert args[0] == "https://127.0.0.1/receive/users/xyz"
        assert "aes_key" in args[1]
        assert "encrypted_magic_envelope" in args[1]
        assert kwargs['headers'] == {'Content-Type': 'application/json'}

        # Ensure public payloads and recipients, one per unique host
        args1, kwargs1 = mock_send.call_args_list[1]
        args2, kwargs2 = mock_send.call_args_list[2]
        public_endpoints = {args1[0], args2[0]}
        assert public_endpoints == {"https://example.net/receive/public", "https://localhost/receive/public"}
        assert args1[1].startswith("<me:env xmlns:me=")
        assert args2[1].startswith("<me:env xmlns:me=")
        assert kwargs1['headers'] == {'Content-Type': 'application/magic-envelope+xml'}
        assert kwargs2['headers'] == {'Content-Type': 'application/magic-envelope+xml'}
