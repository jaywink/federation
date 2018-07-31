from federation.entities.activitypub.constants import CONTEXTS_DEFAULT
from federation.entities.activitypub.entities import ActivitypubProfile


class TestEntitiesConvertToAS2:
    def test_profile_to_as2(self):
        entity = ActivitypubProfile(
            handle="bob@example.com", raw_content="foobar", name="Bob Bobertson", public=True,
            tag_list=["socialfederation", "federation"], image_urls={
                "large": "urllarge", "medium": "urlmedium", "small": "urlsmall"
            }
        )
        result = entity.to_as2()
        assert result.get('@context') == CONTEXTS_DEFAULT + [
            {"manuallyApprovesFollowers": "as:manuallyApprovesFollowers"},
        ]
        assert result.get('type') == 'Person'
