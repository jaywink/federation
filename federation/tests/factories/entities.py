from random import shuffle
import factory
from factory import fuzzy

from federation.entities.base import Post, Profile, Share, Retraction, Image, Follow
from federation.entities.diaspora.entities import DiasporaPost


class ActorIDMixinFactory(factory.Factory):
    actor_id = factory.Faker('uri')


class EntityTypeMixinFactory(factory.Factory):
    entity_type = 'Post'


class IDMixinFactory(factory.Factory):
    id = factory.Faker('uri')


class PublicMixinFactory(factory.Factory):
    public = factory.Faker("pybool")


class TargetIDMixinFactory(factory.Factory):
    target_id = factory.Faker('uri')


class RawContentMixinFactory(factory.Factory):
    raw_content = fuzzy.FuzzyText(length=300)


class FollowFactory(ActorIDMixinFactory, TargetIDMixinFactory):
    class Meta:
        model = Follow

    following = factory.Faker("pybool")


class PostFactory(ActorIDMixinFactory, IDMixinFactory, RawContentMixinFactory, factory.Factory):
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


class ImageFactory(ActorIDMixinFactory, IDMixinFactory, PublicMixinFactory, factory.Factory):
    class Meta:
        model = Image

    remote_path = factory.Faker('uri')
    remote_name = factory.Faker('file_path', extension='jpg')


class ProfileFactory(IDMixinFactory, RawContentMixinFactory, factory.Factory):
    class Meta:
        model = Profile

    name = fuzzy.FuzzyText(length=30)
    public_key = fuzzy.FuzzyText(length=300)


class RetractionFactory(ActorIDMixinFactory, EntityTypeMixinFactory, TargetIDMixinFactory, factory.Factory):
    class Meta:
        model = Retraction


class ShareFactory(ActorIDMixinFactory, EntityTypeMixinFactory, IDMixinFactory, PublicMixinFactory,
                   TargetIDMixinFactory, factory.Factory):
    class Meta:
        model = Share

    raw_content = ""
    provider_display_name = ""
