import re

from federation.entities.base import Image
from federation.entities.mixins import BaseEntity, RawContentMixin
from federation.entities.utils import get_base_attributes


class AttachImagesMixin(RawContentMixin):
    def pre_send(self) -> None:
        """
        Attach any embedded images from the sender server.
        """
        actor_domain = re.match(r"https?://([\w.\-]+)", self.actor_id).groups()[0]
        actor_domain = actor_domain.replace(".", "\\.")
        regex = r"!\[([\w ]*)\]\((https?://%s[\w\/\-.]+\.[jpg|gif|jpeg|png]*)\)" % actor_domain
        matches = re.finditer(regex, self.raw_content, re.MULTILINE | re.IGNORECASE)
        for match in matches:
            groups = match.groups()
            self._children.append(
                Image(
                    url=groups[1],
                    name=groups[0] or "",
                )
            )
        self.raw_content = re.sub(regex, "", self.raw_content, re.MULTILINE | re.IGNORECASE)
        self.raw_content = self.raw_content.strip()


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
