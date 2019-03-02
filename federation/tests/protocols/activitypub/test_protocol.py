import json

from federation.protocols.activitypub.protocol import identify_payload, identify_id


def test_identify_id():
    assert identify_id('foobar') is False
    assert identify_id('foobar@example.com') is False
    assert identify_id('foobar@example.com:8000') is False
    assert identify_id('http://foobar@example.com') is True
    assert identify_id('https://foobar@example.com') is True


class TestIdentifyPayload:
    def test_identifies_activitypub_payload(self):
        assert identify_payload(json.dumps('{"@context": "foo"}'))
        assert identify_payload(json.dumps('{"@context": "foo"}').encode('utf-8'))

    def test_passes_gracefully_for_non_activitypub_payload(self):
        assert not identify_payload('foo')
        assert not identify_payload('<xml></<xml>')
        assert not identify_payload(b'<xml></<xml>')
