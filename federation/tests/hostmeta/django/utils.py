from federation.entities.base import Profile


def get_profile(handle=None, guid=None, request=None):
    return Profile(
        url="https://example.com/profile/1234/",
        atom_url="https://example.com/profile/1234/atom.xml",
        id=f"diaspora://{handle}/profile/1234",
    )
