from typing import Dict, Tuple
from magic import from_file

from dirty_validators.basic import Email

from federation.entities.activitypub.enums import ActivityType
from federation.entities.mixins import (
    PublicMixin, TargetIDMixin, ParticipationMixin, CreatedAtMixin, RawContentMixin, OptionalRawContentMixin,
    EntityTypeMixin, ProviderDisplayNameMixin, RootTargetIDMixin, MediaMixin, BaseEntity)
from federation.utils.network import fetch_file


class Accept(CreatedAtMixin, TargetIDMixin, BaseEntity):
    """An acceptance message for some target."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ID not required for accept
        self._required.remove('id')


class Image(MediaMixin, OptionalRawContentMixin, CreatedAtMixin, BaseEntity):
    """Reflects a single image, possibly linked to another object."""
    height: int = 0
    width: int = 0
    name: str = ""
    inline: bool = False

    _valid_media_types: Tuple[str] = (
        "image/jpeg",
        "image/png",
        "image/gif",
    )

    def get_media_type(self) -> str:
        media_type = super().get_media_type()
        if media_type == 'application/octet-stream':
            try:
                file = fetch_file(self.url)
                media_type = from_file(file, mime=True)
                os.unlink(file)
            except:
                pass
        return media_type


class Audio(MediaMixin, OptionalRawContentMixin, BaseEntity):
    inlineMedia: bool = False

    _valid_media_types: Tuple[str] = (
        "audio/aac",
        "audio/mpeg",
        "audio/ogg",
        "audio/wav",
        "audio/webm"
    )

class Video(MediaMixin, OptionalRawContentMixin, BaseEntity):
    inlineMedia: bool = False

    _valid_media_types: Tuple[str] = (
        "video/mp4",
        "video/mpeg",
        "video/ogg",
        "video/x-msvideo",
        "video/webm",
    )
    

class Comment(RawContentMixin, ParticipationMixin, CreatedAtMixin, RootTargetIDMixin, BaseEntity):
    """Represents a comment, linked to another object."""
    participation = "comment"
    url = ""

    _allowed_children = (Image,)
    _default_activity = ActivityType.CREATE


class Follow(CreatedAtMixin, TargetIDMixin, BaseEntity):
    """Represents a handle following or unfollowing another handle."""
    following = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._required += ["following"]
        # ID not required for follow
        self._required.remove('id')


class Post(RawContentMixin, PublicMixin, CreatedAtMixin, ProviderDisplayNameMixin, BaseEntity):
    """Reflects a post, status message, etc, which will be composed from the message or to the message."""
    location = ""
    url = ""

    _allowed_children = (Image,)
    _default_activity = ActivityType.CREATE


class Reaction(ParticipationMixin, CreatedAtMixin, BaseEntity):
    """Represents a reaction to another object, for example a like."""
    participation = "reaction"
    reaction = ""

    _default_activity = ActivityType.CREATE
    _reaction_valid_values = ["like"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._required += ["reaction"]

    def validate_reaction(self):
        """Ensure reaction is of a certain type.

        Mainly for future expansion.
        """
        if self.reaction not in self._reaction_valid_values:
            raise ValueError("reaction should be one of: {valid}".format(
                valid=", ".join(self._reaction_valid_values)
            ))


class Relationship(CreatedAtMixin, TargetIDMixin, BaseEntity):
    """Represents a relationship between two handles."""
    relationship = ""

    _relationship_valid_values = ["sharing", "following", "ignoring", "blocking"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._required += ["relationship"]

    def validate_relationship(self):
        """Ensure relationship is of a certain type."""
        if self.relationship not in self._relationship_valid_values:
            raise ValueError("relationship should be one of: {valid}".format(
                valid=", ".join(self._relationship_valid_values)
            ))


class Profile(CreatedAtMixin, OptionalRawContentMixin, PublicMixin, BaseEntity):
    """Represents a profile for a user."""
    atom_url = ""
    email = ""
    gender = ""
    image_urls = None
    image = None
    location = ""
    name = ""
    nsfw = False
    public_key = ""
    tag_list = None
    url = ""
    username = ""
    inboxes: Dict = None

    _allowed_children = (Image,)

    def __init__(self, *args, **kwargs):
        self.image_urls = {
            "small": "", "medium": "", "large": ""
        }
        self.inboxes = {
            "private": None,
            "public": None,
        }
        self.tag_list = []
        super().__init__(*args, **kwargs)
        # As an exception, a Profile does not require to have an `actor_id`
        self._required.remove('actor_id')

    def validate_email(self):
        if self.email:
            validator = Email()
            if not validator.is_valid(self.email):
                raise ValueError("Email is not valid")


class Retraction(CreatedAtMixin, TargetIDMixin, EntityTypeMixin, BaseEntity):
    """Represents a retraction of content by author."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ID not required for retraction
        self._required.remove('id')


class Share(CreatedAtMixin, TargetIDMixin, EntityTypeMixin, OptionalRawContentMixin, PublicMixin,
            ProviderDisplayNameMixin, BaseEntity):
    """Represents a share of another entity.

    ``entity_type`` defaults to "Post" but can be any base entity class name. It should be the class name of the
    entity that was shared.

    The optional ``raw_content`` can be used for a "quoted share" case where the sharer adds their own note to the
    share.
    """
    entity_type = "Post"


class Collection(BaseEntity):
    """Represents collections of objects.

    Only useful to Activitypub outbound payloads.
    """
    ordered = False
    total_items = 0
    items = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._required.remove('actor_id')
        self._required += ['ordered']
