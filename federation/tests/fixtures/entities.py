import pytest
from freezegun import freeze_time

from federation.entities.activitypub.entities import (
    ActivitypubPost, ActivitypubAccept, ActivitypubFollow, ActivitypubProfile, ActivitypubComment,
    ActivitypubRetraction, ActivitypubShare)
from federation.entities.base import Profile
from federation.entities.diaspora.entities import (
    DiasporaPost, DiasporaComment, DiasporaLike, DiasporaProfile, DiasporaRetraction,
    DiasporaContact, DiasporaReshare,
)
from federation.tests.factories.entities import ShareFactory
from federation.tests.fixtures.keys import PUBKEY
from federation.tests.fixtures.payloads import DIASPORA_PUBLIC_PAYLOAD


@pytest.fixture
def activitypubannounce():
    with freeze_time("2019-08-05"):
        return ActivitypubShare(
            activity_id="http://127.0.0.1:8000/post/123456/#create",
            actor_id="http://127.0.0.1:8000/profile/123456/",
            target_id="http://127.0.0.1:8000/post/012345/",
        )

@pytest.fixture
def activitypubcomment():
    with freeze_time("2019-04-27"):
        return ActivitypubComment(
            raw_content="raw_content",
            public=True,
            provider_display_name="Socialhome",
            id=f"http://127.0.0.1:8000/post/123456/",
            activity_id=f"http://127.0.0.1:8000/post/123456/#create",
            actor_id=f"http://127.0.0.1:8000/profile/123456/",
            target_id="http://127.0.0.1:8000/post/012345/",
        )


@pytest.fixture
def activitypubfollow():
    return ActivitypubFollow(
        activity_id="https://localhost/follow",
        actor_id="https://localhost/profile",
        target_id="https://example.com/profile",
    )


@pytest.fixture
def activitypubaccept(activitypubfollow):
    return ActivitypubAccept(
        activity_id="https://localhost/accept",
        actor_id="https://localhost/profile",
        target_id="https://example.com/follow/1234",
        object=activitypubfollow.to_as2(),
    )


@pytest.fixture
def activitypubpost():
    with freeze_time("2019-04-27"):
        return ActivitypubPost(
            raw_content="raw_content",
            public=True,
            provider_display_name="Socialhome",
            id=f"http://127.0.0.1:8000/post/123456/",
            activity_id=f"http://127.0.0.1:8000/post/123456/#create",
            actor_id=f"http://127.0.0.1:8000/profile/123456/",
        )


@pytest.fixture
def activitypubprofile():
    return ActivitypubProfile(
        id="https://example.com/bob", raw_content="foobar", name="Bob Bobertson", public=True,
        tag_list=["socialfederation", "federation"], image_urls={
            "large": "urllarge", "medium": "urlmedium", "small": "urlsmall"
        }, inboxes={
            "private": "https://example.com/bob/private",
            "public": "https://example.com/public",
        }, public_key=PUBKEY, url="https://example.com/bob-bobertson"
    )


@pytest.fixture
def activitypubretraction():
    with freeze_time("2019-04-27"):
        return ActivitypubRetraction(
            target_id="http://127.0.0.1:8000/post/123456/",
            activity_id="http://127.0.0.1:8000/post/123456/#delete",
            actor_id="http://127.0.0.1:8000/profile/123456/",
            entity_type="Post",
        )


@pytest.fixture
def activitypubundofollow():
    return ActivitypubFollow(
        activity_id="https://localhost/undo",
        actor_id="https://localhost/profile",
        target_id="https://example.com/profile",
        following=False,
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
        inboxes={
            "private": "https://example.com/bob/private",
            "public": "https://example.com/public",
        }, public_key=PUBKEY,
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
def diasporanestedcomment():
    return DiasporaComment(
        raw_content="raw_content",
        signature="signature",
        id="guid",
        guid="guid",
        actor_id="alice@example.com",
        handle="alice@example.com",
        target_id="thread_target_guid",
        target_guid="thread_target_guid",
        root_target_id="target_guid",
        root_target_guid="target_guid",
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
