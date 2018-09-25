from federation.entities.mixins import BaseEntity
from federation.entities.utils import get_base_attributes


class ActivitypubEntityMixin(BaseEntity):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._required.extend(['activity', 'activity_id'])

    @classmethod
    def from_base(cls, entity):
        # noinspection PyArgumentList
        return cls(**get_base_attributes(entity))

    def get_activity_id(self):
        # noinspection PyUnresolvedReferences
        return f"{self.id}/{self.activity.value}/{self.activity_id}"

    def to_string(self):
        # noinspection PyUnresolvedReferences
        return str(self.to_as2())
