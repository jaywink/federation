import pytest
# noinspection PyPackageRequirements
from freezegun import freeze_time
from unittest.mock import patch

from federation.entities.activitypub.mappers import get_outbound_entity
import federation.entities.activitypub.models as models
from federation.entities.base import Profile, Post, Comment, Retraction
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
        return models.Announce(
            id="http://127.0.0.1:8000/post/123456/#create",
            actor_id="http://127.0.0.1:8000/profile/123456/",
            target_id="http://127.0.0.1:8000/post/012345/",
        )


@pytest.fixture
def activitypubcomment():
    with freeze_time("2019-04-27"):
        obj = models.Comment(
            raw_content="raw_content",
            rendered_content="<p>raw_content</p>",
            public=True,
            provider_display_name="Socialhome",
            id=f"http://127.0.0.1:8000/post/123456/",
            activity_id=f"http://127.0.0.1:8000/post/123456/#create",
            actor_id=f"http://127.0.0.1:8000/profile/123456/",
            target_id="http://127.0.0.1:8000/post/012345/",
        )
        obj.times={'edited':False, 'created':obj.created_at}
        return obj


@pytest.fixture
def activitypubfollow():
    return models.Follow(
        activity_id="https://localhost/follow",
        actor_id="https://localhost/profile",
        target_id="https://example.com/profile",
    )


@pytest.fixture
def activitypubaccept(activitypubfollow):
    return models.Accept(
        activity_id="https://localhost/accept",
        actor_id="https://localhost/profile",
        target_id="https://example.com/follow/1234",
        object_=activitypubfollow,
    )


@pytest.fixture
def activitypubpost():
    with freeze_time("2019-04-27"):
        obj = models.Post(
            raw_content="# raw_content",
            public=True,
            provider_display_name="Socialhome",
            id=f"http://127.0.0.1:8000/post/123456/",
            activity_id=f"http://127.0.0.1:8000/post/123456/#create",
            actor_id=f"http://127.0.0.1:8000/profile/123456/",
            _media_type="text/markdown",
            to=["https://www.w3.org/ns/activitystreams#Public"],
            cc=["https://http://127.0.0.1:8000/profile/123456/followers/"]
        )
        obj.times={'edited':False, 'created':obj.created_at}
        return obj


@pytest.fixture
def activitypubpost_diaspora_guid():
    with freeze_time("2019-04-27"):
        obj = models.Post(
            raw_content="raw_content",
            public=True,
            provider_display_name="Socialhome",
            id=f"http://127.0.0.1:8000/post/123456/",
            activity_id=f"http://127.0.0.1:8000/post/123456/#create",
            actor_id=f"http://127.0.0.1:8000/profile/123456/",
            guid="totallyrandomguid",
        )
        obj.times={'edited':False, 'created':obj.created_at}
        return obj


@pytest.fixture
def activitypubpost_images():
    with freeze_time("2019-04-27"):
        obj = models.Post(
            raw_content="raw_content",
            public=True,
            provider_display_name="Socialhome",
            id=f"http://127.0.0.1:8000/post/123456/",
            activity_id=f"http://127.0.0.1:8000/post/123456/#create",
            actor_id=f"http://127.0.0.1:8000/profile/123456/",
            _children=[
                models.Image(url="foobar", media_type="image/jpeg"),
                models.Image(url="barfoo", name="spam and eggs", media_type="image/jpeg"),
            ],
        )
        obj.times={'edited':False, 'created':obj.created_at}
        return obj


@pytest.fixture
def activitypubpost_mentions():
    with freeze_time("2019-04-27"):
        obj = models.Post(
            raw_content="""# raw_content\n\n@someone@localhost.local @jaywink@localhost.local""",
            public=True,
            provider_display_name="Socialhome",
            id=f"http://127.0.0.1:8000/post/123456/",
            activity_id=f"http://127.0.0.1:8000/post/123456/#create",
            actor_id=f"http://127.0.0.1:8000/profile/123456/",
#            _mentions={
#                "http://127.0.0.1:8000/profile/999999",
#                "jaywink@localhost.local",
#                "http://localhost.local/someone",
#            }
        )
        obj.times={'edited':False, 'created':obj.created_at}
        return obj


@pytest.fixture
def activitypubpost_tags():
    with freeze_time("2019-04-27"):
        obj = models.Post(
            raw_content="# raw_content\n#foobar\n#barfoo",
            public=True,
            provider_display_name="Socialhome",
            id=f"http://127.0.0.1:8000/post/123456/",
            activity_id=f"http://127.0.0.1:8000/post/123456/#create",
            actor_id=f"http://127.0.0.1:8000/profile/123456/",
        )
        obj.times={'edited':False, 'created':obj.created_at}
        return obj


@pytest.fixture
def activitypubpost_embedded_images():
    with freeze_time("2019-04-27"):
        obj = models.Post(
            raw_content="""
#Cycling #lauttasaari #sea #sun


![](https://example.com/media/uploads/2019/07/16/daa24d89-cedf-4fc7-bad8-74a902541476.jpeg)![](https://jasonrobinson.me/media/uploads/2019/07/16/daa24d89-cedf-4fc7-bad8-74a902541477.png)

![foobar](https://jasonrobinson.me/media/uploads/2019/07/16/daa24d89-cedf-4fc7-bad8-74a902541478.gif)
![foobar barfoo](https://jasonrobinson.me/media/uploads/2019/07/16/daa24d89-cedf-4fc7-bad8-74a902541479.jpg)

#only a link, not embedded
[foo](https://jasonrobinson.me/media/uploads/2019/07/16/daa24d89-cedf-4fc7-bad8-74a9025414710.jpg)
#only a link, not embedded
https://jasonrobinson.me/media/uploads/2019/07/16/daa24d89-cedf-4fc7-bad8-74a9025414711.jpg
""",
            public=True,
            provider_display_name="Socialhome",
            id=f"http://127.0.0.1:8000/post/123456/",
            activity_id=f"http://127.0.0.1:8000/post/123456/#create",
            actor_id=f"https://jasonrobinson.me/u/jaywink/",
        )
        obj.times={'edited':False, 'created':obj.created_at}
        return obj


@pytest.fixture
@patch.object(models.base.Image, 'get_media_type', return_value="image/jpeg")
def activitypubprofile(mock_fetch):
    with freeze_time("2022-09-06"):
        return models.Person(
            id="https://example.com/bob", raw_content="foobar", name="Bob Bobertson", public=True,
            tag_list=["socialfederation", "federation"], image_urls={
                "large": "urllarge", "medium": "urlmedium", "small": "urlsmall"
            }, inboxes={
                "private": "https://example.com/bob/private",
                "public": "https://example.com/public",
                }, public_key=PUBKEY, url="https://example.com/bob-bobertson"
        )


@pytest.fixture
@patch.object(models.base.Image, 'get_media_type', return_value="image/jpeg")
def activitypubprofile_diaspora_guid(mock_fetch):
    with freeze_time("2022-09-06"):
        return models.Person(
            id="https://example.com/bob", raw_content="foobar", name="Bob Bobertson", public=True,
            tag_list=["socialfederation", "federation"], image_urls={
                "large": "urllarge", "medium": "urlmedium", "small": "urlsmall"
            }, inboxes={
                "private": "https://example.com/bob/private",
                "public": "https://example.com/public",
            }, public_key=PUBKEY, url="https://example.com/bob-bobertson",
            guid="totallyrandomguid", handle="bob@example.com",
        )


@pytest.fixture
def activitypubretraction():
    with freeze_time("2019-04-27"):
        obj = Retraction(
            target_id="http://127.0.0.1:8000/post/123456/",
            activity_id="http://127.0.0.1:8000/post/123456/#delete",
            actor_id="http://127.0.0.1:8000/profile/123456/",
            entity_type="Post",
        )
        return get_outbound_entity(obj, None)


@pytest.fixture
def activitypubretraction_announce():
    with freeze_time("2019-04-27"):
        obj = Retraction(
            id="http://127.0.0.1:8000/post/123456/activity",
            target_id="http://127.0.0.1:8000/post/123456",
            activity_id="http://127.0.0.1:8000/post/123456/#delete",
            actor_id="http://127.0.0.1:8000/profile/123456/",
            entity_type="Share",
        )
        return get_outbound_entity(obj, None)


@pytest.fixture
def activitypubundofollow():
    return models.Follow(
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
        }, public_key=PUBKEY, to=["https://www.w3.org/ns/activitystreams#Public"],
        url="https://example.com/alice"
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
def diasporacomment_activitypub_id():
    return DiasporaComment(
        raw_content="raw_content",
        signature="signature",
        id="https://domain.tld/id",
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
def diasporapost_activitypub_id():
    return DiasporaPost(
        raw_content="raw_content",
        public=True,
        provider_display_name="Socialhome",
        id="https://domain.tld/id",
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
def diasporaprofile_activitypub_id():
    return DiasporaProfile(
        raw_content="foobar", name="Bob Bobertson", public=True,
        tag_list=["socialfederation", "federation"], image_urls={
            "large": "urllarge", "medium": "urlmedium", "small": "urlsmall"
        },
        id="http://example.com/alice",
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


@pytest.fixture
def post():
    return models.Post(
        raw_content="""One more test before sleep 😅 This time with an image.

![](https://jasonrobinson.me/media/uploads/2020/12/27/1b2326c6-554c-4448-9da3-bdacddf2bb77.jpeg)""",
        public=True,
        provider_display_name="Socialhome",
        id="guid",
        guid="guid",
        actor_id="alice@example.com",
        handle="alice@example.com",
    )


@pytest.fixture
def share():
    return ShareFactory()
