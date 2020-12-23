import json

from federation.protocols.matrix.protocol import identify_request, identify_id
from federation.types import RequestType


def test_identify_id():
    assert identify_id('foobar') is False
    assert identify_id('foobar@example.com') is False
    assert identify_id('foobar@example.com:8000') is False
    assert identify_id('http://foobar@example.com') is False
    assert identify_id('https://foobar@example.com') is False
    assert identify_id('@foobar:domain.tld') is True
    assert identify_id('#foobar:domain.tld') is True
    assert identify_id('!foobar:domain.tld') is True


class TestIdentifyRequest:
    def test_identifies_matrix_request(self):
        assert identify_request(RequestType(body=json.dumps('{"events": []}')))
        assert identify_request(RequestType(body=json.dumps('{"events": []}').encode('utf-8')))

    def test_passes_gracefully_for_non_matrix_request(self):
        assert not identify_request(RequestType(body='foo'))
        assert not identify_request(RequestType(body='<xml></<xml>'))
        assert not identify_request(RequestType(body=b'<xml></<xml>'))
        assert not identify_request(RequestType(body=json.dumps('{"@context": "foo"}')))
        assert not identify_request(RequestType(body=json.dumps('{"@context": "foo"}').encode('utf-8')))
