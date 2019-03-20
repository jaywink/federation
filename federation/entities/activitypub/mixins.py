from federation.entities.mixins import BaseEntity
from federation.entities.utils import get_base_attributes


class ActivitypubEntityMixin(BaseEntity):
    _type = None

    @classmethod
    def from_base(cls, entity):
        # noinspection PyArgumentList
        return cls(**get_base_attributes(entity))

    def to_string(self):
        # noinspection PyUnresolvedReferences
        return str(self.to_as2())


class ActivitypubActorMixin(ActivitypubEntityMixin):
    pass


class ActivitypubObjectMixin(ActivitypubEntityMixin):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._required.append('activity_id')
