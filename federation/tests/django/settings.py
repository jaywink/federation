SECRET_KEY = "foobar"

INSTALLED_APPS = tuple()

FEDERATION = {
    "base_url": "https://example.com",
    "get_object_function": "federation.tests.django.utils.get_object_function",
    "get_profile_function": "federation.tests.django.utils.get_profile",
    "search_path": "/search?q=",
}
