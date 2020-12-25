from federation.protocols.matrix.appservice import get_registration_config, print_registration_yaml


def test_get_registration():
    config = get_registration_config()
    assert config == {
        "id": "uniqueid",
        "url": "https://example.com/matrix",
        "as_token": "secret_token",
        "hs_token": "secret_token",
        "sender_localpart": "_myawesomeapp",
        "namespaces": {
            "users": [
                {
                    "exclusive": False,
                    "regex": "@.*",
                },
                {
                    "exclusive": True,
                    "regex": "@_myawesomeapp_.*",
                },
            ],
            "aliases": [
                {
                    "exclusive": False,
                    "regex": "#.*",
                },
                {
                    "exclusive": True,
                    "regex": "#_myawesomeapp_.*",
                },
            ],
            "rooms": [],
        }
    }


def test_print_registration_yaml():
    """
    Just execute and ensure doesn't crash.
    """
    print_registration_yaml()
