import hashlib
import hmac
import uuid
from typing import Dict, Optional

import requests

from federation.utils.django import get_function_from_config


def generate_dendrite_mac(shared_secret: str, username: str, password: str, admin: bool) -> str:
    """
    Generate a MAC for using in registering users with Dendrite.
    """
    # From: https://github.com/matrix-org/dendrite/blob/master/clientapi/routing/register.go
    mac = hmac.new(
      key=shared_secret.encode('utf8'),
      digestmod=hashlib.sha1,
    )

    mac.update(username.encode('utf8'))
    mac.update(b"\x00")
    mac.update(password.encode('utf8'))
    mac.update(b"\x00")
    mac.update(b"admin" if admin else b"notadmin")
    return mac.hexdigest()


def get_matrix_configuration() -> Optional[Dict]:
    """
    Return Matrix configuration.

    Requires Django support currently.
    """
    try:
        matrix_config_func = get_function_from_config("matrix_config_function")
    except AttributeError:
        raise AttributeError("Not configured for Matrix support")
    return matrix_config_func()


def register_dendrite_user(username: str) -> Dict:
    """
    Shared secret registration for Dendrite.

    Note uses the legacy route, see
    https://github.com/matrix-org/dendrite/issues/1669

    Currently compatible with Django apps only.

    Returns:
        {
            'user_id': '@username:domain.tld',
            'access_token': 'randomaccesstoken',
            'home_server': 'domain.tld',
            'device_id': 'randomdevice'
        }
    """
    matrix_config = get_matrix_configuration

    password = str(uuid.uuid4())
    mac = generate_dendrite_mac(
        matrix_config["registration_shared_secret"],
        username,
        password,
        False,
    )

    # Register using shared secret
    response = requests.post(
        f"{matrix_config['homeserver_base_url']}/_matrix/client/api/v1/register?kind=user",
        json={
            "type": "org.matrix.login.shared_secret",
            "mac": mac,
            "password": password,
            "user": username,
            "admin": False,
        },
        headers={
            "Content-Type": "application/json",
        },
    )
    response.raise_for_status()
    return response.json()
