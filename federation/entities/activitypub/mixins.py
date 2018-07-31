from federation.entities.utils import get_base_attributes


class ActivitypubEntityMixin:
    @classmethod
    def from_base(cls, entity):
        # noinspection PyArgumentList
        return cls(**get_base_attributes(entity))

    def get_activity_id(self, activity):
        # noinspection PyUnresolvedReferences
        return f"{self.id}/{activity.lower()}"

    def to_string(self):
        # noinspection PyUnresolvedReferences
        return str(self.to_as2())
