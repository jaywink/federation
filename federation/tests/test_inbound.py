from unittest.mock import AsyncMock, patch

import pytest

from federation.exceptions import NoSuitableProtocolFoundError
from federation.inbound import handle_receive
from federation.protocols.diaspora.protocol import Protocol
from federation.tests.fixtures.payloads import DIASPORA_PUBLIC_PAYLOAD
from federation.types import RequestType


class TestHandleReceiveProtocolIdentification:
    async def test_handle_receive_routes_to_identified_protocol(self):
        payload = RequestType(body=DIASPORA_PUBLIC_PAYLOAD)
        with patch.object(
                    Protocol,
                    'receive', new_callable=AsyncMock,
                    return_value=("foobar@domain.tld", "<foobar></foobar>")) as mock_receive,\
                patch(
                    "federation.entities.diaspora.mappers.message_to_objects", new_callable=AsyncMock,
                    return_value=[]) as mock_message_to_objects:
            await handle_receive(payload)
            assert mock_receive.called

    async def test_handle_receive_raises_on_unidentified_protocol(self):
        payload = RequestType(body="foobar")
        with pytest.raises(NoSuitableProtocolFoundError):
            await handle_receive(payload)
