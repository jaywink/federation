# -*- coding: utf-8 -*-
from unittest.mock import Mock, patch

from Crypto.PublicKey import RSA

from federation.entities.diaspora.entities import DiasporaPost
from federation.outbound import handle_create_payload


class TestHandleCreatePayloadBuildsAPayload(object):
    def test_handle_create_payload_builds_an_xml(self):
        from_user = Mock(private_key=RSA.generate(2048), handle="foobar@domain.tld")
        to_user = Mock(key=RSA.generate(2048).publickey())
        entity = DiasporaPost()
        data = handle_create_payload(from_user, to_user, entity)
        assert len(data) > 0
        parts = data.split("=")
        assert len(parts) == 2
        assert parts[0] == "xml"
        assert len(parts[1]) > 0

    @patch("federation.outbound.get_outbound_entity")
    def test_handle_create_payload_calls_get_outbound_entity(self, mock_get_outbound_entity):
        mock_get_outbound_entity.return_value = DiasporaPost()
        from_user = Mock(private_key=RSA.generate(2048), handle="foobar@domain.tld")
        to_user = Mock(key=RSA.generate(2048).publickey())
        entity = DiasporaPost()
        handle_create_payload(from_user, to_user, entity)
        assert mock_get_outbound_entity.called
