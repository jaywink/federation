from federation.utils.diaspora import generate_diaspora_profile_id


def get_profile_id_by_handle(handle):
    return generate_diaspora_profile_id(handle, "1234")
