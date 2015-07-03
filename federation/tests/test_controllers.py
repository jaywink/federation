from unittest.mock import patch
import pytest

from federation.controllers import handle_receive
from federation.exceptions import NoSuitableProtocolFoundError
from federation.tests.fixtures.payloads import UNENCRYPTED_DIASPORA_PAYLOAD


class TestHandleReceiveProtocolIdentification(object):

    @patch("federation.protocols.diaspora.protocol.Protocol")
    def test_handle_receive_routes_to_identified_protocol(self, MockProtocol):
        payload = UNENCRYPTED_DIASPORA_PAYLOAD
        handle_receive(payload)
        assert MockProtocol.called

    def test_handle_receive_raises_on_unidentified_protocol(self):
        payload = "foobar"
        with pytest.raises(NoSuitableProtocolFoundError):
            handle_receive(payload)
