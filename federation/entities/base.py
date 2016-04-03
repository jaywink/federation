# -*- coding: utf-8 -*-
from datetime import datetime
from dirty_validators.basic import Email


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
        # TBD
        pass


class GUIDMixin(BaseEntity):
    guid = ""

    def __init__(self, *args, **kwargs):
        super(GUIDMixin, self).__init__(*args, **kwargs)
        self._required += ["guid"]

    def validate_guid(self):
        if len(self.guid) < 16:
            raise ValueError("GUID must be at least 16 characters")


class HandleMixin(BaseEntity):
    handle = ""

    def __init__(self, *args, **kwargs):
        super(HandleMixin, self).__init__(*args, **kwargs)
        self._required += ["handle"]

    def validate_handle(self):
        validator = Email()
        if not validator.is_valid(self.handle):
            raise ValueError("Handle is not valid")


class PublicMixin(BaseEntity):
    public = False


class CreatedAtMixin(BaseEntity):
    created_at = datetime.now()

    def __init__(self, *args, **kwargs):
        super(CreatedAtMixin, self).__init__(*args, **kwargs)
        self._required += ["created_at"]


class Post(GUIDMixin, HandleMixin, PublicMixin, CreatedAtMixin, BaseEntity):
    """Reflects a post, status message, etc, which will be composed from the message or to the message."""
    raw_content = ""
    provider_display_name = ""
    location = ""
    photos = []

    def __init__(self, *args, **kwargs):
        super(Post, self).__init__(*args, **kwargs)
        self._required += ["raw_content"]

    @property
    def tags(self):
        """Returns a `set` of unique tags contained in `raw_content`."""
        return set({word.strip("#") for word in self.raw_content.split() if word.startswith("#")})


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
        super(Image, self).__init__(*args, **kwargs)
        self._required += ["remote_path", "remote_name"]
