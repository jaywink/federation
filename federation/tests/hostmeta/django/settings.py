SECRET_KEY = "foobar"

INSTALLED_APPS = tuple()

FEDERATION = {
    "base_url": "https://example.com",
    "profile_id_function": "federation.tests.hostmeta.django.utils.get_profile_id_by_handle",
}
