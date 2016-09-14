from Crypto import Random
from Crypto.PublicKey import RSA
from lxml.etree import _Element

from federation.protocols.diaspora.magic_envelope import MagicEnvelope
from federation.tests.fixtures.keys import get_dummy_private_key


class TestMagicEnvelope(object):
    @staticmethod
    def generate_rsa_private_key():
        """Generate a new RSA private key."""
        rand = Random.new().read
        return RSA.generate(2048, rand)

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
            author_handle="foobar@example.com"
        )
        payload = env.create_payload()
        assert payload == "PHN0YXR1c19tZXNzYWdlPjxmb28-YmFyPC9mb28-PC9zdGF0dXNfbWVzc2FnZT4="

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
