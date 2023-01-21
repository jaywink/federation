from federation.protocols.activitypub.signing import get_http_authentication
from federation.tests.fixtures.keys import get_dummy_private_key


def test_signing_request():
    key = get_dummy_private_key()
    auth = get_http_authentication(key, "dummy_key_id")
    assert auth.header_signer.headers == [
        '(request-target)',
        'user-agent',
        'host',
        'date',
        'digest',
    ]
    assert auth.header_signer.secret == key.exportKey()
    assert 'dummy_key_id' in auth.header_signer.signature_template

