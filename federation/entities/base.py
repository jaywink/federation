# -*- coding: utf-8 -*-
import datetime

from dirty_validators.basic import Email


__all__ = ("Post", "Image", "Comment")


class BaseEntity(object):
    _required = []

    def __init__(self, *args, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)

    def validate(self):
        """Do validation.

        1) Loop through attributes and call their `validate_<attr>` methods, if any.
        2) Check `_required` contents and make sure all attrs in there have a value.
        """
        attributes = []
        for attr in dir(self):
            if not attr.startswith("_"):
                attr_type = type(getattr(self, attr))
                if attr_type != "method":
                    if getattr(self, "validate_{attr}".format(attr=attr), None):
                        getattr(self, "validate_{attr}".format(attr=attr))()
                    attributes.append(attr)
        required_fulfilled = set(self._required).issubset(set(attributes))
        if not required_fulfilled:
            raise ValueError(
                "Not all required attributes fulfilled. Required: {required}".format(required=self._required)
            )


class GUIDMixin(BaseEntity):
    guid = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._required += ["guid"]

    def validate_guid(self):
        if len(self.guid) < 16:
            raise ValueError("GUID must be at least 16 characters")


class HandleMixin(BaseEntity):
    handle = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._required += ["handle"]

    def validate_handle(self):
        validator = Email()
        if not validator.is_valid(self.handle):
            raise ValueError("Handle is not valid")


class PublicMixin(BaseEntity):
    public = False


class CreatedAtMixin(BaseEntity):
    created_at = datetime.datetime.now()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._required += ["created_at"]


class RawContentMixin(BaseEntity):
    raw_content = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._required += ["raw_content"]

    @property
    def tags(self):
        """Returns a `set` of unique tags contained in `raw_content`."""
        if not self.raw_content:
            return set()
        return set({word.strip("#") for word in self.raw_content.split() if word.startswith("#")})


class Post(RawContentMixin, GUIDMixin, HandleMixin, PublicMixin, CreatedAtMixin, BaseEntity):
    """Reflects a post, status message, etc, which will be composed from the message or to the message."""
    provider_display_name = ""
    location = ""
    photos = []


class Image(GUIDMixin, HandleMixin, PublicMixin, CreatedAtMixin, BaseEntity):
    """Reflects a single image, possibly linked to another object."""
    remote_path = ""
    remote_name = ""
    text = ""
    linked_type = ""
    linked_guid = ""
    height = 0
    width = 0

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._required += ["remote_path", "remote_name"]


class ParticipationMixin(BaseEntity):
    """Reflects a participation to something."""
    target_guid = ""
    participation = ""

    _participation_valid_values = ["reaction", "subscription", "comment"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._required += ["target_guid", "participation"]

    def validate_participation(self):
        """Ensure participation is of a certain type."""
        if self.participation not in self._participation_valid_values:
            raise ValueError("participation should be one of: {valid}".format(
                valid=", ".join(self._participation_valid_values)
            ))


class Comment(RawContentMixin, GUIDMixin, ParticipationMixin, CreatedAtMixin, HandleMixin):
    """Represents a comment, linked to another object."""
    participation = "comment"


class Reaction(GUIDMixin, ParticipationMixin, CreatedAtMixin, HandleMixin):
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
