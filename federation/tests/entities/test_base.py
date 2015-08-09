from federation.tests.factories.entities import TaggedPostFactory


class TestPostEntityTags(object):

    def test_post_entity_returns_list_of_tags(self):
        post = TaggedPostFactory()
        assert post.tags == {"tagone", "tagtwo", "tagthree"}
