SECRET_KEY = "foobar"

INSTALLED_APPS = tuple()

FEDERATION = {
    "base_url": "https://example.com",
    "get_object_function": "federation.tests.django.utils.get_object_function",
    "get_profile_function": "federation.tests.django.utils.get_profile",
    "process_payload_function": "federation.tests.django.utils.process_payload",
    "search_path": "/search?q=",
}
