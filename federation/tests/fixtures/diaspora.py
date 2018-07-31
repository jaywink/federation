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
        raw_content="raw_content",
        signature="signature",
        id="diaspora://alice@example.com/comment/guid",
        actor_id="diaspora://alice@example.com/profile/guid",
        target_id="diaspora://bob@example.org/status_message/target_guid",
    )


@pytest.fixture
def diasporacontact():
    return DiasporaContact(
        actor_id="diaspora://alice@example.com/contact/guid",
        target_id="diaspora://bob@example.org/profile/target_guid",
        following=True,
    )


@pytest.fixture
def diasporalike():
    return DiasporaLike(
        id="diaspora://alice@example.com/like/guid",
        actor_id="diaspora://alice@example.com/profile/guid",
        target_id="diaspora://bob@example.org/status_message/target_guid",
        signature="signature",
    )


@pytest.fixture
def diasporapost():
    return DiasporaPost(
        raw_content="raw_content",
        public=True,
        provider_display_name="Socialhome",
        id="diaspora://alice@example.com/status_message/guid",
        actor_id="diaspora://alice@example.com/profile/guid",
    )


@pytest.fixture
def diasporaprofile():
    return DiasporaProfile(
        raw_content="foobar", name="Bob Bobertson", public=True,
        tag_list=["socialfederation", "federation"], image_urls={
            "large": "urllarge", "medium": "urlmedium", "small": "urlsmall"
        },
        id="diaspora://alice@example.com/profile/guid",
    )


@pytest.fixture
def diasporareshare():
    base_entity = ShareFactory()
    return DiasporaReshare.from_base(base_entity)


@pytest.fixture
def diasporaretraction():
    return DiasporaRetraction(
        actor_id="diaspora://alice@example.com/profile/guid",
        target_id="diaspora://alice@example.com/status_message/target_guid",
        entity_type="Post",
    )
