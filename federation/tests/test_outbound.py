from unittest.mock import Mock, patch

import pytest

from federation.entities.diaspora.entities import DiasporaPost
from federation.outbound import handle_create_payload, handle_send
from federation.tests.fixtures.keys import get_dummy_private_key
from federation.types import UserType
from federation.utils.text import encode_if_text


class TestHandleCreatePayloadBuildsAPayload:
    @patch("federation.protocols.diaspora.protocol.MagicEnvelope", autospec=True)
    def test_handle_create_payload___diaspora__calls_magic_envelope_render(self, mock_me):
        mock_render = Mock()
        mock_me.return_value = Mock(render=mock_render)
        author_user = Mock()
        entity = DiasporaPost()
        entity.validate = Mock()
        handle_create_payload(entity, author_user, "diaspora")
        mock_render.assert_called_once_with()


@patch("federation.outbound.send_document")
class TestHandleSend:
    def test_calls_handle_create_payload(self, mock_send, profile):
        key = get_dummy_private_key()
        recipients = [
            {
                "endpoint": "https://127.0.0.1/receive/users/1234", "public_key": key.publickey(), "public": False,
                "protocol": "diaspora", "fid": "",
            },
            {
                "endpoint": "https://example.com/receive/public", "public": True, "protocol": "diaspora",
                "fid": "",
            },
            {
                "endpoint": "https://example.net/receive/public", "public": True, "protocol": "diaspora",
                "fid": "",
            },
            # Same twice to ensure one delivery only per unique
            {
                "endpoint": "https://example.net/receive/public", "public": True, "protocol": "diaspora",
                "fid": "",
            },
            {
                "endpoint": "https://example.net/foobar/inbox", "fid": "https://example.net/foobar", "public": False,
                "protocol": "activitypub",
            },
            {
                "endpoint": "https://example.net/inbox", "fid": "https://example.net/foobar", "public": True,
                "protocol": "activitypub",
            }
        ]
        author = UserType(
            private_key=key, id="foo@example.com", handle="foo@example.com",
        )
        handle_send(profile, author, recipients)

        # Ensure first call is a private diaspora payload
        args, kwargs = mock_send.call_args_list[0]
        assert args[0] == "https://127.0.0.1/receive/users/1234"
        assert "aes_key" in args[1]
        assert "encrypted_magic_envelope" in args[1]
        assert kwargs['headers'] == {'Content-Type': 'application/json'}

        # Ensure second call is a private activitypub payload
        args, kwargs = mock_send.call_args_list[1]
        assert args[0] == "https://example.net/foobar/inbox"
        assert kwargs['headers'] == {
            'Content-Type': 'application/ld+json; profile="https://www.w3.org/ns/activitystreams"',
        }
        assert encode_if_text("https://www.w3.org/ns/activitystreams#Public") not in args[1]

        # Ensure third call is a public activitypub payload
        args, kwargs = mock_send.call_args_list[2]
        assert args[0] == "https://example.net/inbox"
        assert kwargs['headers'] == {
            'Content-Type': 'application/ld+json; profile="https://www.w3.org/ns/activitystreams"',
        }
        assert encode_if_text("https://www.w3.org/ns/activitystreams#Public") in args[1]

        # Ensure diaspora public payloads and recipients, one per unique host
        args3, kwargs3 = mock_send.call_args_list[3]
        args4, kwargs4 = mock_send.call_args_list[4]
        public_endpoints = {args3[0], args4[0]}
        assert public_endpoints == {
            "https://example.net/receive/public",
            "https://example.com/receive/public",
        }
        assert args3[1].startswith("<me:env xmlns:me=")
        assert args4[1].startswith("<me:env xmlns:me=")
        assert kwargs3['headers'] == {'Content-Type': 'application/magic-envelope+xml'}
        assert kwargs4['headers'] == {'Content-Type': 'application/magic-envelope+xml'}

        with pytest.raises(IndexError):
            # noinspection PyStatementEffect
            mock_send.call_args_list[5]

    def test_survives_sending_share_if_diaspora_payload_cannot_be_created(self, mock_send, share):
        key = get_dummy_private_key()
        share.target_handle = None  # Ensure diaspora payload fails
        recipients = [
            {
                "endpoint": "https://example.com/receive/public", "public": True, "protocol": "diaspora",
                "fid": "",
            },
            {
                "endpoint": "https://example.tld/receive/public", "public": True, "protocol": "diaspora",
                "fid": "",
            },
            {
                "endpoint": "https://example.net/inbox", "fid": "https://example.net/foobar", "public": True,
                "protocol": "activitypub",
            }
        ]
        author = UserType(
            private_key=key, id="foo@example.com", handle="foo@example.com",
        )
        handle_send(share, author, recipients)

        # Ensure first call is a public activitypub payload
        args, kwargs = mock_send.call_args_list[0]
        assert args[0] == "https://example.net/inbox"
        assert kwargs['headers'] == {
            'Content-Type': 'application/ld+json; profile="https://www.w3.org/ns/activitystreams"',
        }
        assert encode_if_text("https://www.w3.org/ns/activitystreams#Public") in args[1]

        # Should only be one call
        assert mock_send.call_count == 1
