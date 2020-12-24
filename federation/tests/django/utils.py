from typing import Dict

# noinspection PyPackageRequirements
from Crypto.PublicKey.RSA import RsaKey

from federation.entities.base import Profile
from federation.tests.fixtures.keys import get_dummy_private_key


def dummy_profile():
    return Profile(
        url=f"https://example.com/profile/1234/",
        atom_url=f"https://example.com/profile/1234/atom.xml",
        id=f"https://example.com/p/1234/",
        handle="foobar@example.com",
        guid="1234",
        name="Bob Bobértson",
    )


def get_object_function(object_id):
    return dummy_profile()


def get_private_key(identifier: str) -> RsaKey:
    return get_dummy_private_key()


def get_profile(fid=None, handle=None, guid=None, request=None):
    return dummy_profile()


def matrix_config_func() -> Dict:
    return {
        "homeserver_base_url": "https://matrix.domain.tld",
        "homeserver_domain_with_port": "matrix.domain.tld:443",
        "homeserver_name": "domain.tld",
        "appservice": {
            "id": "uniqueid",
            "shortcode": "myawesomeapp",
            "token": "secret_token",
        },
        "identity_server_base_url": "https://id.domain.tld",
        "client_wellknown_other_keys": {
            "org.foo.key" "barfoo",
        },
        "registration_shared_secret": "supersecretstring",
    }


def process_payload(request):
    return True
