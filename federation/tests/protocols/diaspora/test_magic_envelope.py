from unittest.mock import patch, Mock

import pytest
from lxml import etree
from lxml.etree import _Element

from federation.exceptions import SignatureVerificationError
from federation.protocols.diaspora.magic_envelope import MagicEnvelope
from federation.tests.fixtures.keys import get_dummy_private_key, PUBKEY
from federation.tests.fixtures.payloads import DIASPORA_PUBLIC_PAYLOAD


class TestMagicEnvelope:
    def test_build(self):
        env = MagicEnvelope(
            message="<status_message><foo>bar</foo></status_message>",
            private_key=get_dummy_private_key(),
            author_handle="foobar@example.com"
        )
        doc = env.build()
        assert isinstance(doc, _Element)

    def test_create_payload_wrapped(self):
        env = MagicEnvelope(
            message="<status_message><foo>bar</foo></status_message>",
            private_key="key",
            author_handle="foobar@example.com",
            wrap_payload=True,
        )
        payload = env.create_payload()
        assert payload == "PFhNTD48cG9zdD48c3RhdHVzX21lc3NhZ2U-PGZvbz5iYXI8L2Zvbz48L3N0YXR1c19tZXNzYWdlPjwvcG9zdD4" \
                          "8L1hNTD4="

    def test_create_payload(self):
        env = MagicEnvelope(
            message="<status_message><foo>bar</foo></status_message>",
            private_key="key",
            author_handle="foobar@example.com",
        )
        payload = env.create_payload()
        assert payload == "PHN0YXR1c19tZXNzYWdlPjxmb28-YmFyPC9mb28-PC9zdGF0dXNfbWVzc2FnZT4="

    def test_extract_payload(self, diaspora_public_payload):
        env = MagicEnvelope()
        env.payload = diaspora_public_payload
        assert not env.doc
        assert not env.author_handle
        assert not env.message
        env.extract_payload()
        assert isinstance(env.doc, _Element)
        assert env.author_handle == "foobar@example.com"
        assert env.message == b"<status_message><foo>bar</foo></status_message>"

    @patch("federation.protocols.diaspora.magic_envelope.fetch_public_key", autospec=True)
    def test_fetch_public_key__calls_sender_key_fetcher(self, mock_fetch):
        mock_fetcher = Mock(return_value="public key")
        env = MagicEnvelope(author_handle="spam@eggs", sender_key_fetcher=mock_fetcher)
        env.fetch_public_key()
        mock_fetcher.assert_called_once_with("spam@eggs")
        assert not mock_fetch.called

    @patch("federation.protocols.diaspora.magic_envelope.fetch_public_key", autospec=True)
    def test_fetch_public_key__calls_fetch_public_key(self, mock_fetch):
        env = MagicEnvelope(author_handle="spam@eggs")
        env.fetch_public_key()
        mock_fetch.assert_called_once_with("spam@eggs")

    def test_message_from_doc(self, diaspora_public_payload):
        env = MagicEnvelope(payload=diaspora_public_payload)
        assert env.message_from_doc() == env.message

    def test_payload_extracted_on_init(self, diaspora_public_payload):
        env = MagicEnvelope(payload=diaspora_public_payload)
        assert isinstance(env.doc, _Element)
        assert env.author_handle == "foobar@example.com"
        assert env.message == b"<status_message><foo>bar</foo></status_message>"

    def test_verify(self, private_key, public_key):
        me = MagicEnvelope(
            message="<status_message><foo>bar</foo></status_message>",
            private_key=private_key,
            author_handle="foobar@example.com"
        )
        me.build()
        output = me.render()

        MagicEnvelope(payload=output, public_key=public_key, verify=True)

        with pytest.raises(SignatureVerificationError):
            MagicEnvelope(payload=output, public_key=PUBKEY, verify=True)

    def test_verify__calls_fetch_public_key(self, diaspora_public_payload):
        me = MagicEnvelope(payload=diaspora_public_payload)
        with pytest.raises(TypeError):
            with patch.object(me, "fetch_public_key") as mock_fetch:
                me.verify()
                mock_fetch.assert_called_once_with()

    @patch("federation.protocols.diaspora.magic_envelope.MagicEnvelope.verify")
    def test_verify_on_init(self, mock_verify, diaspora_public_payload):
        MagicEnvelope(payload=diaspora_public_payload)
        assert not mock_verify.called
        MagicEnvelope(payload=diaspora_public_payload, verify=True)
        assert mock_verify.called

    def test_build_signature(self):
        env = MagicEnvelope(
            message="<status_message><foo>bar</foo></status_message>",
            private_key=get_dummy_private_key(),
            author_handle="foobar@example.com"
        )
        env.create_payload()
        signature, key_id = env._build_signature()
        assert signature == b'Cmk08MR4Tp8r9eVybD1hORcR_8NLRVxAu0biOfJbkI1xLx1c480zJ720cpVyKaF9CxVjW3lvlvRz' \
                            b'5YbswMv0izPzfHpXoWTXH-4UPrXaGYyJnrNvqEB2UWn4iHKJ2Rerto8sJY2b95qbXD6Nq75EoBNu' \
                            b'b5P7DYc16ENhp38YwBRnrBEvNOewddpOpEBVobyNB7no_QR8c_xkXie-hUDFNwI0z7vax9HkaBFb' \
                            b'vEmzFPMZAAdWyjxeGiWiqY0t2ZdZRCPTezy66X6Q0qc4I8kfT-Mt1ctjGmNMoJ4Lgu-PrO5hSRT4' \
                            b'QBAVyxaog5w-B0PIPuC-mUW5SZLsnX3_ZuwJww=='
        assert key_id == b"Zm9vYmFyQGV4YW1wbGUuY29t"

    def test_render(self):
        env = MagicEnvelope(
            message="<status_message><foo>bar</foo></status_message>",
            private_key=get_dummy_private_key(),
            author_handle="foobar@example.com"
        )
        env.build()
        output = env.render()
        assert output == '<me:env xmlns:me="http://salmon-protocol.org/ns/magic-env"><me:encoding>base64url' \
                         '</me:encoding><me:alg>RSA-SHA256</me:alg><me:data type="application/xml">' \
                         'PHN0YXR1c19tZXNzYWdlPjxmb28-YmFyPC9mb28-PC9zdGF0dXNfbWVzc2FnZT4=</me:data>' \
                         '<me:sig key_id="Zm9vYmFyQGV4YW1wbGUuY29t">Cmk08MR4Tp8r9eVybD1hORcR_8NLRVxAu0biOfJbk' \
                         'I1xLx1c480zJ720cpVyKaF9CxVjW3lvlvRz5YbswMv0izPzfHpXoWTXH-4UPrXaGYyJnrNvqEB2UWn4iHK' \
                         'J2Rerto8sJY2b95qbXD6Nq75EoBNub5P7DYc16ENhp38YwBRnrBEvNOewddpOpEBVobyNB7no_QR8c_xkX' \
                         'ie-hUDFNwI0z7vax9HkaBFbvEmzFPMZAAdWyjxeGiWiqY0t2ZdZRCPTezy66X6Q0qc4I8kfT-Mt1ctjGmNM' \
                         'oJ4Lgu-PrO5hSRT4QBAVyxaog5w-B0PIPuC-mUW5SZLsnX3_ZuwJww==</me:sig></me:env>'
        env2 = MagicEnvelope(
            message="<status_message><foo>bar</foo></status_message>",
            private_key=get_dummy_private_key(),
            author_handle="foobar@example.com"
        )
        output2 = env2.render()
        assert output2 == output

    def test_get_sender(self):
        doc = etree.fromstring(bytes(DIASPORA_PUBLIC_PAYLOAD, encoding="utf-8"))
        assert MagicEnvelope.get_sender(doc) == "foobar@example.com"
