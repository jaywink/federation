from federation.utils.diaspora import generate_diaspora_profile_id


def get_profile_by_handle(handle):
    return {
        "id": generate_diaspora_profile_id(handle, "1234"),
        "profile_path": "/profile/1234/",
    }
