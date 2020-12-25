from typing import Dict

import yaml

from federation.utils.django import get_configuration
from federation.utils.matrix import get_matrix_configuration


def get_registration_config() -> Dict:
    """
    Get registration config.

    Requires Django support currently.
    """
    config = get_configuration()
    matrix_config = get_matrix_configuration()

    if not matrix_config.get("appservice"):
        raise Exception("No appservice configured")

    return {
        "id": matrix_config["appservice"]["id"],
        "url": f"{config['base_url']}/matrix",
        "as_token": matrix_config["appservice"]["token"],
        "hs_token": matrix_config["appservice"]["token"],
        "sender_localpart": f'_{matrix_config["appservice"]["shortcode"]}',
        "namespaces": {
            # We reserve two namespaces
            # One is not exclusive, since we're interested in events of "real" users
            # One is exclusive, the ones that represent "remote to us but managed by us towards Matrix"
            "users": [
                {
                    "exclusive": False,
                    "regex": "@.*",
                },
                {
                    "exclusive": True,
                    "regex": f"@_{matrix_config['appservice']['shortcode']}_.*"
                },
            ],
            "aliases": [
                {
                    "exclusive": False,
                    "regex": "#.*",
                },
                {
                    "exclusive": True,
                    "regex": f"#_{matrix_config['appservice']['shortcode']}_.*"
                },
            ],
            "rooms": [],
        }
    }


def print_registration_yaml():
    """
    Print registration file details.

    Requires Django support currently.
    """
    registration = get_registration_config()
    print(yaml.safe_dump(registration))
