from federation.entities.base import Profile


def get_object_function(object_id):
    return Profile(
        url=f"https://example.com/profile/1234/",
        atom_url=f"https://example.com/profile/1234/atom.xml",
        id=f"https://example.com/profile/1234/",
        handle="foobar@example.com",
        guid="1234",
        name="Bob Bobértson",
    )


def get_profile(handle=None, request=None):
    return Profile(
        url=f"https://example.com/profile/1234/",
        atom_url=f"https://example.com/profile/1234/atom.xml",
        id=f"https://example.com/profile/1234/",
        handle="foobar@example.com",
        guid="1234",
    )
