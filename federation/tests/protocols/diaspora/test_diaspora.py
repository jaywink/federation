from lxml import etree

from federation.protocols.diaspora.protocol import DiasporaProtocol


class MockUser(object):
    key = "foobar"


class TestDiasporaProtocol():

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

    def init_protocol(self):
        return DiasporaProtocol()

    def get_unencrypted_doc(self):
        return etree.fromstring("""<?xml version='1.0'?>
            <diaspora xmlns="https://joindiaspora.com/protocol" xmlns:me="http://salmon-protocol.org/ns/magic-env">
                <header>
                    <author_id>{author}</author_id>
                </header>
                <!-- {magic_envelope} -->
            </diaspora>
        """)

    def get_encrypted_doc(self):
        return etree.fromstring("""<?xml version='1.0'?>
            <diaspora xmlns="https://joindiaspora.com/protocol" xmlns:me="http://salmon-protocol.org/ns/magic-env">
                <encrypted_header>{encrypted_header}</encrypted_header>
                <!-- {magic_envelope with encrypted data} -->
            </diaspora>
        """)

    def get_mock_user(self):
        return MockUser()

    def mock_parse_encrypted_header(self, text, key):
        if text and key:
            return "{encrypted_header}"
        return None
