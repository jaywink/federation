from federation.entities.activitypub.constants import (
    CONTEXTS_DEFAULT, CONTEXT_MANUALLY_APPROVES_FOLLOWERS, CONTEXT_LD_SIGNATURES, CONTEXT_HASHTAG, CONTEXT_SENSITIVE)
from federation.entities.activitypub.entities import ActivitypubProfile


class TestEntitiesConvertToAS2:
    def test_post_to_as2(self, activitypubpost):
        # TODO expand
        result = activitypubpost.to_as2()
        assert result.get('@context') == CONTEXTS_DEFAULT + [
            CONTEXT_HASHTAG,
            CONTEXT_SENSITIVE,
        ]
        assert result.get('type') == 'Note'

    def test_profile_to_as2(self):
        # TODO expand
        entity = ActivitypubProfile(
            handle="bob@example.com", raw_content="foobar", name="Bob Bobertson", public=True,
            tag_list=["socialfederation", "federation"], image_urls={
                "large": "urllarge", "medium": "urlmedium", "small": "urlsmall"
            }
        )
        result = entity.to_as2()
        assert result.get('@context') == CONTEXTS_DEFAULT + [
            CONTEXT_LD_SIGNATURES,
            CONTEXT_MANUALLY_APPROVES_FOLLOWERS,
        ]
        assert result.get('type') == 'Person'
