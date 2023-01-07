from unittest.mock import Mock, DEFAULT

import pytest
import inspect
import requests

# noinspection PyUnresolvedReferences
from federation.tests.fixtures.entities import *
from federation.tests.fixtures.types import *
from federation.tests.fixtures.keys import get_dummy_private_key


@pytest.fixture(autouse=True)
def disable_network_calls(monkeypatch):
    """Disable network calls."""
    monkeypatch.setattr("requests.post", Mock())

    class MockGetResponse(str):
        status_code = 200
        text = ""

        @staticmethod
        def raise_for_status():
            pass

    saved_get = requests.get
    def side_effect(*args, **kwargs):
        if "pyld/documentloader" in inspect.stack()[4][1]:
            return saved_get(*args, **kwargs)
        return DEFAULT

    monkeypatch.setattr("requests.get", Mock(return_value=MockGetResponse, side_effect=side_effect))

    class MockHeadResponse(dict):
        status_code = 200
        headers = {'Content-Type':'image/jpeg'}

        @staticmethod
        def raise_for_status():
            pass

    monkeypatch.setattr("requests.head", Mock(return_value=MockHeadResponse))

@pytest.fixture
def private_key():
    return get_dummy_private_key()


@pytest.fixture
def public_key(private_key):
    return private_key.publickey().exportKey()
