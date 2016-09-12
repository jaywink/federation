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
        assert payload == b"<XML><post><status_message><foo>bar</foo></status_message></post></XML>"

    def test_create_payload(self):
        env = MagicEnvelope(
            message="<status_message><foo>bar</foo></status_message>",
            private_key="key",
            author_handle="foobar@example.com"
        )
        payload = env.create_payload()
        assert payload == b"<status_message><foo>bar</foo></status_message>"

    def test_encode_payload(self):
        env = MagicEnvelope(
            message="<status_message><foo>bar</foo></status_message>",
            private_key="key",
            author_handle="foobar@example.com"
        )
        env.create_payload()
        payload = env._encode_payload()
        assert payload == "PHN0YXR1c19tZXNzYWdlPjxmb28-YmFyPC9mb28-PC9zdGF0dXNfbWVzc2Fn\nZT4=\n"

    def test_build_signature(self):
        env = MagicEnvelope(
            message="<status_message><foo>bar</foo></status_message>",
            private_key=get_dummy_private_key(),
            author_handle="foobar@example.com"
        )
        env.create_payload()
        env._encode_payload()
        signature, key_id = env._build_signature()
        assert signature == b"RAfiBBrk0OzPbmh6xE7wMRe7ir-qprZ7zk5VDGfopc6rfATFNbNB2FWH" \
                            b"FdvJfoky9ORNvfUoiFmtbMG7kmmFHgpQdUl_OU81lKb7NG6-aq2ZRVDQ" \
                            b"T46UYat1ssdqkkynqywowdyEGVUxxalFkOHWuYajmpc7ajt_G8xXjMDU" \
                            b"Ctt0VUFXepxshd24ZWRXO1RQK4bFr7X9-d26Ho3kLuB1VB_pYYbxJQCZl" \
                            b"m0EDlFj7vktl0zibswMFyRqiacwu8zec_HR4x8yMkF_zSNJsnnLq6ch4ad6" \
                            b"r83LOVk3Yvdxinb61spHEjr2zvPWExEgUt4Jcpc07aZRUKCJVfFXFYAGnA=="
        assert key_id == b"Zm9vYmFyQGV4YW1wbGUuY29t"

    def test_render(self):
        env = MagicEnvelope(
            message="<status_message><foo>bar</foo></status_message>",
            private_key=get_dummy_private_key(),
            author_handle="foobar@example.com"
        )
        env.build()
        output = env.render()
        assert output == '<me:env xmlns:me="http://salmon-protocol.org/ns/magic-env">' \
                         '<me:encoding>base64url</me:encoding><me:alg>RSA-SHA256</me:alg>' \
                         '<me:data type="application/xml">PHN0YXR1c19tZXNzYWdlPjxmb28-Ym' \
                         'FyPC9mb28-PC9zdGF0dXNfbWVzc2Fn\nZT4=\n</me:data>' \
                         '<me:sig key_id="Zm9vYmFyQGV4YW1wbGUuY29t">RAfiBBrk0OzPbmh6xE7wMRe' \
                         '7ir-qprZ7zk5VDGfopc6rfATFNbNB2FWHFdvJfoky9ORNvfUoiFmtbMG7kmmFHgp' \
                         'QdUl_OU81lKb7NG6-aq2ZRVDQT46UYat1ssdqkkynqywo' \
                         'wdyEGVUxxalFkOHWuYajmpc7ajt_G8xXjMDUCtt0VUFXepxshd24ZWRX' \
                         'O1RQK4bFr7X9-d26Ho3kLuB1VB_pYYbxJQCZlm0EDlFj7vktl0zibs' \
                         'wMFyRqiacwu8zec_HR4x8yMkF_zSNJsnnLq6ch4ad6r83LOVk3Yvdxin' \
                         'b61spHEjr2zvPWExEgUt4Jcpc07aZRUKCJVfFXFYAGnA==</me:sig></me:env>'
        env2 = MagicEnvelope(
            message="<status_message><foo>bar</foo></status_message>",
            private_key=get_dummy_private_key(),
            author_handle="foobar@example.com"
        )
        output2 = env2.render()
        assert output2 == output
