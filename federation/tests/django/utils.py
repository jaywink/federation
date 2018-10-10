from federation.entities.base import Profile


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


def get_profile(handle=None, request=None):
    return dummy_profile()


def process_payload(request):
    return True
