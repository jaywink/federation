SECRET_KEY = "foobar"

INSTALLED_APPS = tuple()

FEDERATION = {
    "base_url": "https://example.com",
    "get_profile_function": "federation.tests.hostmeta.django.utils.get_profile",
    "search_path": "/search?q=",
}
