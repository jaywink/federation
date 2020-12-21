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
        "url": f"{config['base_url']}/matrix/appservice",
        "as_token": matrix_config["appservice"]["token"],
        "hs_token": matrix_config["appservice"]["token"],
        "sender_localpart": matrix_config["appservice"]["sender_localpart"],
        "namespaces": {
            "users": [
                {
                    "exclusive": False,
                    "regex": "@.*",
                },
            ],
            "aliases": [
                {
                    "exclusive": False,
                    "regex": "#.*",
                }
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
