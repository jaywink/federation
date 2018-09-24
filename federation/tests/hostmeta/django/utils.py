from federation.entities.base import Profile


def get_profile(handle=None, request=None):
    return Profile(
        url=f"https://example.com/profile/1234/",
        atom_url=f"https://example.com/profile/1234/atom.xml",
        id=f"diaspora://{handle}/profile/1234",
        handle=handle,
        guid="1234",
    )
