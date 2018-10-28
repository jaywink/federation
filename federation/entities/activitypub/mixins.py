from federation.entities.activitypub.enums import ActorType
from federation.entities.mixins import BaseEntity
from federation.entities.utils import get_base_attributes


class ActivitypubEntityMixin(BaseEntity):
    _type = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self._type not in ActorType.values():
            self._required.append('activity_id')

    @classmethod
    def from_base(cls, entity):
        # noinspection PyArgumentList
        return cls(**get_base_attributes(entity))

    def to_string(self):
        # noinspection PyUnresolvedReferences
        return str(self.to_as2())
