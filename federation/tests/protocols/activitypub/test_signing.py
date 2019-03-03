from federation.protocols.activitypub.signing import get_http_authentication
from federation.tests.fixtures.keys import get_dummy_private_key


def test_signing_request():
    key = get_dummy_private_key().exportKey()
    auth = get_http_authentication(key, "dummy_key_id")
    assert auth.algorithm == 'rsa-sha256'
    assert auth.headers == [
        '(request-target)',
        'user-agent',
        'host',
        'date',
    ]
    assert auth.key == key
    assert auth.key_id == 'dummy_key_id'

