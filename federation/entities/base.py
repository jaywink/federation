from dirty_validators.basic import Email

from federation.entities.mixins import (
    PublicMixin, TargetIDMixin, ParticipationMixin, CreatedAtMixin, RawContentMixin, OptionalRawContentMixin,
    EntityTypeMixin, ProviderDisplayNameMixin)


class Image(PublicMixin, OptionalRawContentMixin, CreatedAtMixin):
    """Reflects a single image, possibly linked to another object."""
    remote_path = ""
    remote_name = ""
    linked_type = ""
    linked_guid = ""
    height = 0
    width = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._required += ["remote_path", "remote_name"]


class Comment(RawContentMixin, ParticipationMixin, CreatedAtMixin):
    """Represents a comment, linked to another object."""
    participation = "comment"

    _allowed_children = (Image,)


class Follow(CreatedAtMixin, TargetIDMixin):
    """Represents a handle following or unfollowing another handle."""
    following = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._required += ["following"]
        # ID not required for follow
        self._required.remove('id')


class Post(RawContentMixin, PublicMixin, CreatedAtMixin, ProviderDisplayNameMixin):
    """Reflects a post, status message, etc, which will be composed from the message or to the message."""
    location = ""

    _allowed_children = (Image,)


class Reaction(ParticipationMixin, CreatedAtMixin):
    """Represents a reaction to another object, for example a like."""
    participation = "reaction"
    reaction = ""

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


class Relationship(CreatedAtMixin, TargetIDMixin):
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


class Profile(CreatedAtMixin, OptionalRawContentMixin, PublicMixin):
    """Represents a profile for a user."""
    atom_url = ""
    email = ""
    gender = ""
    image_urls = None
    location = ""
    name = ""
    nsfw = False
    public_key = ""
    tag_list = None
    url = ""

    _allowed_children = (Image,)

    def __init__(self, *args, **kwargs):
        self.image_urls = {
            "small": "", "medium": "", "large": ""
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


class Retraction(CreatedAtMixin, TargetIDMixin, EntityTypeMixin):
    """Represents a retraction of content by author."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # ID not required for retraction
        self._required.remove('id')


class Share(CreatedAtMixin, TargetIDMixin, EntityTypeMixin, OptionalRawContentMixin, PublicMixin,
            ProviderDisplayNameMixin):
    """Represents a share of another entity.

    ``entity_type`` defaults to "Post" but can be any base entity class name. It should be the class name of the
    entity that was shared.

    The optional ``raw_content`` can be used for a "quoted share" case where the sharer adds their own note to the
    share.
    """
    entity_type = "Post"
