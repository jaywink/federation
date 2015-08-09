from random import shuffle
import factory
from factory import fuzzy

from federation.entities.base import Post


class GUIDMixinFactory(factory.Factory):
    guid = fuzzy.FuzzyText(length=32)


class HandleMixinFactory(factory.Factory):
    handle = fuzzy.FuzzyText(length=8, suffix="@example.com")


class PostFactory(GUIDMixinFactory, HandleMixinFactory, factory.Factory):
    class Meta:
        model = Post

    raw_content = fuzzy.FuzzyText(length=300)


class TaggedPostFactory(PostFactory):

    @factory.lazy_attribute
    def raw_content(self):
        parts = []
        for tag in ["tagone", "tagtwo", "tagthree", "tagthree"]:  # Yes, three is twice for fun
            parts.append(fuzzy.FuzzyText(length=50).fuzz())
            parts.append("#%s" % tag)
        shuffle(parts)
        return " ".join(parts)
