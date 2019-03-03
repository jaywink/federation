from federation.utils.protocols import identify_recipient_protocol


def test_identify_recipient_protocol():
    assert identify_recipient_protocol("https://example.com/foo") == "activitypub"
    assert identify_recipient_protocol("http://example.com/foo") == "activitypub"
    assert identify_recipient_protocol("http://127.0.0.1/foo") == "activitypub"
    assert identify_recipient_protocol("http://localhost/foo") == "activitypub"
    assert identify_recipient_protocol("ftp://example.com/foo") is None
    assert identify_recipient_protocol("foo@example.com") == "diaspora"
    assert identify_recipient_protocol("foo@127.0.0.1") == "diaspora"
    assert identify_recipient_protocol("foo@localhost") is None
    assert identify_recipient_protocol("@foo@example.com") is None
    assert identify_recipient_protocol("@foo:example.com") is None
