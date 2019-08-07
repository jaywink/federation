import re

from federation.entities.mixins import BaseEntity, RawContentMixin
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


class CleanContentMixin(RawContentMixin):
    def post_receive(self) -> None:
        """
        Make linkified Mastodon tags normal tags.
        """
        def cleaner(match):
            return f"#{match.groups()[0]}"

        self.raw_content = re.sub(
            r'<a href=\"https://[\w/\.]+\">#<span>([a-zA-Z0-9-_]+)</span></a>', cleaner, self.raw_content, re.MULTILINE,
        )
