# -*- coding: utf-8 -*-
from unittest.mock import patch, Mock
from Crypto.PublicKey import RSA
import pytest

from federation.controllers import handle_receive, handle_create_payload
from federation.entities.base import Post
from federation.exceptions import NoSuitableProtocolFoundError
from federation.protocols.diaspora.protocol import Protocol
from federation.tests.fixtures.payloads import UNENCRYPTED_DIASPORA_PAYLOAD


class TestHandleReceiveProtocolIdentification(object):

    def test_handle_receive_routes_to_identified_protocol(self):
        payload = UNENCRYPTED_DIASPORA_PAYLOAD
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


class TestHandleCreatePayloadBuildsAPayload(object):

    def test_handle_create_payload_builds_an_xml(self):
        from_user = Mock(private_key=RSA.generate(2048), handle="foobar@domain.tld")
        to_user = Mock(key=RSA.generate(2048).publickey())
        entity = Post()
        data = handle_create_payload(from_user, to_user, entity)
        assert len(data) > 0
        parts = data.split("=")
        assert len(parts) == 2
        assert parts[0] == "xml"
        assert len(parts[1]) > 0
