import pytest

from federation.tests.fixtures.keys import get_dummy_private_key
from federation.types import UserType


@pytest.fixture
def usertype():
    return UserType(
        id="https://localhost/profile",
        private_key=get_dummy_private_key(),
    )
