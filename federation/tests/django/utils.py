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


def get_profile(handle=None, request=None):
    return dummy_profile()


def process_payload(request):
    return True
