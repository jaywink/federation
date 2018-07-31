import pytest

from federation.entities.diaspora.entities import (
    DiasporaPost, DiasporaComment, DiasporaLike, DiasporaProfile, DiasporaRetraction,
    DiasporaContact, DiasporaReshare,
)
from federation.tests.factories.entities import ShareFactory
from federation.tests.fixtures.payloads import DIASPORA_PUBLIC_PAYLOAD

__all__ = ("diasporacomment", "diasporacontact", "diasporalike", "diasporapost", "diasporaprofile",
           "diasporareshare", "diasporaretraction", "diaspora_public_payload")


@pytest.fixture
def diaspora_public_payload():
    return DIASPORA_PUBLIC_PAYLOAD


@pytest.fixture
def diasporacomment():
    return DiasporaComment(
        raw_content="raw_content", guid="guid", target_guid="target_guid", handle="handle",
        signature="signature"
    )


@pytest.fixture
def diasporacontact():
    return DiasporaContact(handle="alice@example.com", target_handle="bob@example.org", following=True)


@pytest.fixture
def diasporalike():
    return DiasporaLike(guid="guid", target_guid="target_guid", handle="handle", signature="signature")


@pytest.fixture
def diasporapost():
    return DiasporaPost(
        raw_content="raw_content", guid="guid", handle="handle", public=True,
        provider_display_name="Socialhome"
    )


@pytest.fixture
def diasporaprofile():
    return DiasporaProfile(
        handle="bob@example.com", raw_content="foobar", name="Bob Bobertson", public=True,
        tag_list=["socialfederation", "federation"], image_urls={
            "large": "urllarge", "medium": "urlmedium", "small": "urlsmall"
        }
    )


@pytest.fixture
def diasporareshare():
    base_entity = ShareFactory()
    return DiasporaReshare.from_base(base_entity)


@pytest.fixture
def diasporaretraction():
    return DiasporaRetraction(handle="bob@example.com", target_guid="x" * 16, entity_type="Post")
