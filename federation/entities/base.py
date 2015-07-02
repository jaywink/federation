from federation.entities.fields import TextField, GUIDField, HandleField, BooleanField, DateTimeField


class GUIDMixin(object):
    guid = GUIDField(required=True)


class HandleMixin(object):
    handle = HandleField(required=True)


class BaseEntity(object):
    pass


class PostEntity(GUIDMixin, HandleMixin, BaseEntity):
    """Reflects a post, status message, etc, which will be composed from the message or to the message."""
    raw_content = TextField(required=True)
    public = BooleanField()
    created_at = DateTimeField(required=True)
    provider_display_name = TextField()  # For example, client info
