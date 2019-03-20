import uuid

import pytest

from federation.entities.activitypub.entities import ActivitypubPost, ActivitypubAccept
from federation.entities.base import Profile
from federation.entities.diaspora.entities import (
    DiasporaPost, DiasporaComment, DiasporaLike, DiasporaProfile, DiasporaRetraction,
    DiasporaContact, DiasporaReshare,
)
from federation.tests.factories.entities import ShareFactory
from federation.tests.fixtures.payloads import DIASPORA_PUBLIC_PAYLOAD


@pytest.fixture
def activitypubaccept():
    return ActivitypubAccept(
        activity_id="https://localhost/accept",
        actor_id="https://localhost/profile",
        target_id="https://example.com/follow/1234",
    )


@pytest.fixture
def profile():
    return Profile(
        raw_content="foobar", name="Bob Bobertson", public=True,
        tag_list=["socialfederation", "federation"], image_urls={
            "large": "urllarge", "medium": "urlmedium", "small": "urlsmall"
        },
        id="https://example.com/alice",
        handle="alice@example.com",
        guid="guid",
    )


@pytest.fixture
def diaspora_public_payload():
    return DIASPORA_PUBLIC_PAYLOAD


@pytest.fixture
def diasporacomment():
    return DiasporaComment(
        raw_content="raw_content",
        signature="signature",
        id="guid",
        guid="guid",
        actor_id="alice@example.com",
        handle="alice@example.com",
        target_id="target_guid",
        target_guid="target_guid",
    )


@pytest.fixture
def diasporacontact():
    return DiasporaContact(
        actor_id="alice@example.com",
        handle="alice@example.com",
        target_id="bob@example.org",
        target_handle="bob@example.org",
        following=True,
    )


@pytest.fixture
def diasporalike():
    return DiasporaLike(
        id="guid",
        guid="guid",
        actor_id="alice@example.com",
        handle="alice@example.com",
        target_id="target_guid",
        target_guid="target_guid",
        signature="signature",
    )


@pytest.fixture
def activitypubpost():
    post_uuid = uuid.uuid4()
    profile_uuid = uuid.uuid4()
    return ActivitypubPost(
        raw_content="raw_content",
        public=True,
        provider_display_name="Socialhome",
        id=f"http://127.0.0.1:8000/post/{post_uuid}/",
        guid=post_uuid,
        actor_id=f"http://127.0.0.1:8000/profile/{profile_uuid}/",
        handle="alice@example.com",
    )

@pytest.fixture
def diasporapost():
    return DiasporaPost(
        raw_content="raw_content",
        public=True,
        provider_display_name="Socialhome",
        id="guid",
        guid="guid",
        actor_id="alice@example.com",
        handle="alice@example.com",
    )


@pytest.fixture
def diasporaprofile():
    return DiasporaProfile(
        raw_content="foobar", name="Bob Bobertson", public=True,
        tag_list=["socialfederation", "federation"], image_urls={
            "large": "urllarge", "medium": "urlmedium", "small": "urlsmall"
        },
        id="alice@example.com",
        handle="alice@example.com",
        guid="guid",
    )


@pytest.fixture
def diasporareshare():
    base_entity = ShareFactory()
    return DiasporaReshare.from_base(base_entity)


@pytest.fixture
def diasporaretraction():
    return DiasporaRetraction(
        actor_id="alice@example.com",
        handle="alice@example.com",
        target_id="target_guid",
        target_guid="target_guid",
        entity_type="Post",
    )
