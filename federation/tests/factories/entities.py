from random import shuffle
import factory
from factory import fuzzy

from federation.entities.base import Post, Profile, Share
from federation.entities.diaspora.entities import DiasporaPost


class GUIDMixinFactory(factory.Factory):
    guid = fuzzy.FuzzyText(length=32)


class HandleMixinFactory(factory.Factory):
    handle = fuzzy.FuzzyText(length=8, suffix="@example.com")


class RawContentMixinFactory(factory.Factory):
    raw_content = fuzzy.FuzzyText(length=300)


class PostFactory(GUIDMixinFactory, HandleMixinFactory, RawContentMixinFactory):
    class Meta:
        model = Post


class TaggedPostFactory(PostFactory):

    @factory.lazy_attribute
    def raw_content(self):
        parts = []
        for tag in ["tagone", "tagtwo", "tagthree", "tagthree", "SnakeCase", "UPPER", ""]:
            parts.append(fuzzy.FuzzyText(length=50).fuzz())
            parts.append("#%s" % tag)
        shuffle(parts)
        return " ".join(parts)


class DiasporaPostFactory(PostFactory):
    class Meta:
        model = DiasporaPost


class ProfileFactory(GUIDMixinFactory, HandleMixinFactory, RawContentMixinFactory):
    class Meta:
        model = Profile

    name = fuzzy.FuzzyText(length=30)
    public_key = fuzzy.FuzzyText(length=300)


class ShareFactory(GUIDMixinFactory, HandleMixinFactory):
    class Meta:
        model = Share

    target_guid = factory.Faker("uuid4")
    entity_type = "Post"
    raw_content = ""
    public = factory.Faker("pybool")
    provider_display_name = ""
    target_handle = factory.Faker("safe_email")
