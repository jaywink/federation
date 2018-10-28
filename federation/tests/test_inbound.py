from unittest.mock import patch

import pytest

from federation.exceptions import NoSuitableProtocolFoundError
from federation.inbound import handle_receive
from federation.protocols.diaspora.protocol import Protocol
from federation.tests.fixtures.payloads import DIASPORA_PUBLIC_PAYLOAD


class TestHandleReceiveProtocolIdentification:
    def test_handle_receive_routes_to_identified_protocol(self):
        payload = DIASPORA_PUBLIC_PAYLOAD
        with patch.object(
                    Protocol,
                    'receive',
                    return_value=("foobar@domain.tld", "<foobar></foobar>")) as mock_receive,\
                patch(
                    "federation.entities.diaspora.mappers.message_to_objects",
                    return_value=[]) as mock_message_to_objects:
            handle_receive(payload)
            assert mock_receive.called

    def test_handle_receive_raises_on_unidentified_protocol(self):
        payload = "foobar"
        with pytest.raises(NoSuitableProtocolFoundError):
            handle_receive(payload)
