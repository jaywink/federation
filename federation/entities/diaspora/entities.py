from lxml import etree

from federation.entities.base import (
    Comment, Post, Reaction, Profile, Retraction, Follow, Share, Image)
from federation.entities.diaspora.mixins import DiasporaEntityMixin, DiasporaPreSendMixin, DiasporaRelayableMixin
from federation.entities.diaspora.utils import format_dt, struct_to_xml
from federation.utils.diaspora import get_private_endpoint, get_public_endpoint

class DiasporaComment(DiasporaPreSendMixin, DiasporaRelayableMixin, Comment):
    """Diaspora comment."""
    _tag_name = "comment"

    def to_xml(self):
        element = etree.Element(self._tag_name)
        properties = [
            {"guid": self.guid},
            {"parent_guid": self.root_target_guid or self.target_guid},
            {"thread_parent_guid": self.target_guid},
            {"author_signature": self.signature},
            {"parent_author_signature": self.parent_signature},
            {"text": self.raw_content},
            {"author": self.handle},
            {"created_at": format_dt(self.created_at)},
        ]
        if self.id and self.id.startswith("http"):
            properties.append({
                "activitypub_id": self.id,
            })
        struct_to_xml(element, properties)
        return element


class DiasporaImage(DiasporaEntityMixin, Image):
    _tag_name = "photo"


class DiasporaPost(DiasporaPreSendMixin, DiasporaEntityMixin, Post):
    """Diaspora post, ie status message."""
    _tag_name = "status_message"

    def to_xml(self):
        """Convert to XML message."""
        element = etree.Element(self._tag_name)
        properties = [
            {"text": self.raw_content},
            {"guid": self.guid},
            {"author": self.handle},
            {"public": "true" if self.public else "false"},
            {"created_at": format_dt(self.created_at)},
            {"provider_display_name": self.provider_display_name},
        ]
        if self.id and self.id.startswith("http"):
            properties.append({
                "activitypub_id": self.id,
            })
        struct_to_xml(element, properties)
        return element


class DiasporaLike(DiasporaRelayableMixin, Reaction):
    """Diaspora like."""
    _tag_name = "like"
    reaction = "like"

    def to_xml(self):
        """Convert to XML message."""
        element = etree.Element(self._tag_name)
        struct_to_xml(element, [
            {"parent_type": "Post"},
            {"guid": self.guid},
            {"parent_guid": self.target_guid},
            {"author_signature": self.signature},
            {"parent_author_signature": self.parent_signature},
            {"positive": "true"},
            {"author": self.handle},
        ])
        return element


class DiasporaContact(DiasporaEntityMixin, Follow):
    """Diaspora contact.

    Note we don't implement 'sharing' at the moment so just send it as the same as 'following'.
    """
    _tag_name = "contact"

    def to_xml(self):
        """Convert to XML message."""
        element = etree.Element(self._tag_name)
        struct_to_xml(element, [
            {"author": self.handle},
            {"recipient": self.target_handle},
            {"following": "true" if self.following else "false"},
            {"sharing": "true" if self.following else "false"},
        ])
        return element


class DiasporaProfile(DiasporaEntityMixin, Profile):
    """Diaspora profile."""
    _tag_name = "profile"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.inboxes = {
            "private": get_private_endpoint(self.handle, self.guid),
            "public": get_public_endpoint(self.handle),
        }

    def to_xml(self):
        """Convert to XML message."""
        element = etree.Element(self._tag_name)
        properties = [
            {"author": self.handle},
            {"first_name": self.name},
            {"last_name": ""},  # We only have one field - splitting it would be artificial
            {"image_url": self.image_urls["large"]},
            {"image_url_small": self.image_urls["small"]},
            {"image_url_medium": self.image_urls["medium"]},
            {"gender": self.gender},
            {"bio": self.raw_content},
            {"location": self.location},
            {"searchable": "true" if self.public else "false"},
            {"nsfw": "true" if self.nsfw else "false"},
            {"tag_string": " ".join(["#%s" % tag for tag in self.tag_list])},
        ]
        if self.id and self.id.startswith("http"):
            properties.append({
                "activitypub_id": self.id,
            })
        struct_to_xml(element, properties)
        return element


class DiasporaRetraction(DiasporaEntityMixin, Retraction):
    """Diaspora Retraction."""
    _tag_name = "retraction"
    mapped = {
        "Like": "Reaction",
        "Photo": "Image",
        "Person": "Profile",
    }

    def to_xml(self):
        """Convert to XML message."""
        element = etree.Element(self._tag_name)
        struct_to_xml(element, [
            {"author": self.handle},
            {"target_guid": self.target_guid},
            {"target_type": DiasporaRetraction.entity_type_to_remote(self.entity_type)},
        ])
        return element

    @staticmethod
    def entity_type_from_remote(value):
        """Convert entity type between Diaspora names and our Entity names."""
        if value in DiasporaRetraction.mapped:
            return DiasporaRetraction.mapped[value]
        return value

    @staticmethod
    def entity_type_to_remote(value):
        """Convert entity type between our Entity names and Diaspora names."""
        if value in DiasporaRetraction.mapped.values():
            values = list(DiasporaRetraction.mapped.values())
            index = values.index(value)
            return list(DiasporaRetraction.mapped.keys())[index]
        return value


class DiasporaReshare(DiasporaEntityMixin, Share):
    """Diaspora Reshare."""
    _tag_name = "reshare"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._required += ["target_guid", "target_handle"]

    @staticmethod
    def fill_extra_attributes(attributes):
        """If `public` is missing, add it as True.

        Diaspora removed this from protocol version 0.2.2 so assume all future reshares are public.
        """
        if attributes.get("public") is None:
            attributes["public"] = True
        return attributes

    def to_xml(self):
        element = etree.Element(self._tag_name)
        struct_to_xml(element, [
            {"author": self.handle},
            {"guid": self.guid},
            {"created_at": format_dt(self.created_at)},
            {"root_author": self.target_handle},
            {"root_guid": self.target_guid},
            {"provider_display_name": self.provider_display_name},
            {"public": "true" if self.public else "false"},
            # Some of our own not in Diaspora protocol
            {"text": self.raw_content},
            {"entity_type": self.entity_type},
        ])
        return element
