from unittest.mock import Mock, patch

from federation.entities.diaspora.entities import DiasporaPost
from federation.outbound import handle_create_payload, handle_send
from federation.tests.fixtures.keys import get_dummy_private_key


class TestHandleCreatePayloadBuildsAPayload:
    @patch("federation.protocols.diaspora.protocol.MagicEnvelope", autospec=True)
    def test_handle_create_payload___diaspora__calls_magic_envelope_render(self, mock_me):
        mock_render = Mock()
        mock_me.return_value = Mock(render=mock_render)
        author_user = Mock()
        entity = DiasporaPost()
        handle_create_payload(entity, author_user, "diaspora")
        mock_render.assert_called_once_with()


@patch("federation.outbound.send_document")
class TestHandleSend:
    def test_calls_handle_create_payload(self, mock_send, profile):
        key = get_dummy_private_key()
        recipients = [
            ("foo@127.0.0.1", key.publickey(), "xyz"),
            ("https://127.0.0.1/foobar", key.publickey()),
            ("foo@example.com", None),
            "foo@example.net",
            "qwer@example.net",  # Same host twice to ensure one delivery only per host for public payloads
            "https://example.net/foobar",  # On the same host there is an AP actor
        ]
        mock_author = Mock(
            private_key=key, id="foo@example.com", handle="foo@example.com",
        )
        handle_send(profile, mock_author, recipients)

        # Ensure first call is a private diaspora payload
        args, kwargs = mock_send.call_args_list[0]
        assert args[0] == "https://127.0.0.1/receive/users/xyz"
        assert "aes_key" in args[1]
        assert "encrypted_magic_envelope" in args[1]
        assert kwargs['headers'] == {'Content-Type': 'application/json'}

        # Ensure second call is a private activitypub payload
        args, kwargs = mock_send.call_args_list[1]
        assert args[0] == "https://127.0.0.1/foobar"
        assert kwargs['headers'] == {'Content-Type': 'application/activity+json'}

        # Ensure public payloads and recipients, one per unique host
        args1, kwargs1 = mock_send.call_args_list[2]
        args2, kwargs2 = mock_send.call_args_list[3]
        args3, kwargs3 = mock_send.call_args_list[4]
        public_endpoints = {args1[0], args2[0], args3[0]}
        assert public_endpoints == {
            "https://example.net/receive/public",
            "https://example.com/receive/public",
            "https://example.net/foobar",
        }
        assert args2[1].startswith("<me:env xmlns:me=")
        assert args3[1].startswith("<me:env xmlns:me=")
        assert kwargs1['headers'] == {'Content-Type': 'application/activity+json'}
        assert kwargs2['headers'] == {'Content-Type': 'application/magic-envelope+xml'}
        assert kwargs3['headers'] == {'Content-Type': 'application/magic-envelope+xml'}
