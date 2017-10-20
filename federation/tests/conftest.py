from unittest.mock import Mock

import pytest

from federation.entities.diaspora.entities import DiasporaPost
from federation.tests.fixtures.keys import get_dummy_private_key
from federation.tests.fixtures.payloads import DIASPORA_PUBLIC_PAYLOAD


@pytest.fixture(autouse=True)
def disable_network_calls(monkeypatch):
    """Disable network calls."""
    monkeypatch.setattr("requests.post", Mock())

    class MockResponse(str):
        status_code = 200
        text = ""

        @staticmethod
        def raise_for_status():
            pass

    monkeypatch.setattr("requests.get", Mock(return_value=MockResponse))


@pytest.fixture
def diaspora_public_payload():
    return DIASPORA_PUBLIC_PAYLOAD


@pytest.fixture
def diasporapost():
    return DiasporaPost()


@pytest.fixture
def private_key():
    return get_dummy_private_key()


@pytest.fixture
def public_key(private_key):
    return private_key.publickey().exportKey()
