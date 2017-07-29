from unittest.mock import Mock, patch, call

from Crypto.PublicKey import RSA

from federation.entities.diaspora.entities import DiasporaPost, DiasporaComment
from federation.outbound import handle_create_payload, handle_send


class TestHandleCreatePayloadBuildsAPayload:
    @patch("federation.outbound.Protocol")
    def test_handle_create_payload_builds_an_xml(self, mock_protocol_class):
        mock_protocol = Mock()
        mock_protocol_class.return_value = mock_protocol
        author_user = Mock()
        entity = DiasporaPost()
        handle_create_payload(entity, author_user)
        mock_protocol.build_send.assert_called_once_with(entity=entity, from_user=author_user, to_user=None)

    @patch("federation.outbound.get_outbound_entity")
    def test_handle_create_payload_calls_get_outbound_entity(self, mock_get_outbound_entity):
        mock_get_outbound_entity.return_value = DiasporaPost()
        author_user = Mock(private_key=RSA.generate(2048), handle="foobar@domain.tld")
        entity = DiasporaPost()
        handle_create_payload(entity, author_user)
        mock_get_outbound_entity.assert_called_once_with(entity, author_user.private_key)

    @patch("federation.outbound.get_outbound_entity")
    def test_handle_create_payload_calls_get_outbound_entity_with_author_user(self, mock_get_outbound_entity):
        mock_get_outbound_entity.return_value = DiasporaPost()
        author_user = Mock(private_key=RSA.generate(2048), handle="foobar@domain.tld")
        entity = DiasporaPost()
        handle_create_payload(entity, author_user)
        mock_get_outbound_entity.assert_called_once_with(entity, author_user.private_key)

    @patch("federation.outbound.get_outbound_entity")
    def test_handle_create_payload_calls_sign_with_parent(self, mock_get_outbound_entity):
        comment = DiasporaComment()
        mock_get_outbound_entity.return_value = comment
        author_user = Mock(private_key=RSA.generate(2048), handle="foobar@domain.tld")
        parent_user = Mock(private_key=RSA.generate(2048), handle="parent@domain.tld")
        entity = DiasporaComment()
        with patch.object(comment, "sign_with_parent") as mock_sign:
            handle_create_payload(entity, author_user, parent_user=parent_user)
            mock_sign.assert_called_once_with(parent_user.private_key)


@patch("federation.outbound.handle_create_payload", return_value="payload")
@patch("federation.outbound.send_document")
class TestHandleSend:
    def test_calls_handle_create_payload(self, mock_send, mock_create, diasporapost):
        recipients = [("foo@127.0.0.1", "diaspora"), ("localhost", None)]
        mock_author = Mock()
        handle_send(diasporapost, mock_author, recipients)
        mock_create.assert_called_once_with(diasporapost, mock_author, parent_user=None)
        mock_create.reset_mock()
        handle_send(diasporapost, mock_author, recipients, parent_user="parent_user")
        mock_create.assert_called_once_with(diasporapost, mock_author, parent_user="parent_user")

    def test_calls_send_document(self, mock_send, mock_create, diasporapost):
        recipients = [("foo@127.0.0.1", "diaspora"), ("localhost", None)]
        mock_from_user = Mock()
        handle_send(diasporapost, mock_from_user, recipients)
        call_args_list = [
            call("https://127.0.0.1/receive/public", "payload"),
            call("https://localhost/receive/public", "payload"),
        ]
        assert call_args_list[0] in mock_send.call_args_list
        assert call_args_list[1] in mock_send.call_args_list
