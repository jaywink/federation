from federation.entities.fields import TextField, GUIDField, HandleField, BooleanField, DateTimeField, ListField, \
    IntegerField


class GUIDMixin(object):
    guid = GUIDField(required=True)


class HandleMixin(object):
    handle = HandleField(required=True)


class PublicMixin(object):
    public = BooleanField()


class CreatedAtMixin(object):
    created_at = DateTimeField(required=True)


class BaseEntity(object):
    pass


class PostEntity(GUIDMixin, HandleMixin, PublicMixin, CreatedAtMixin, BaseEntity):
    """Reflects a post, status message, etc, which will be composed from the message or to the message."""
    raw_content = TextField(required=True)
    provider_display_name = TextField()  # For example, client info
    location = TextField()  # Free text of a location
    photos = ListField(type_of=ImageEntity)


class ImageEntity(GUIDMixin, HandleMixin, PublicMixin, CreatedAtMixin, BaseEntity):
    """Reflects a single image, possibly linked to another object."""
    remote_path = TextField(required=True)
    remote_name = TextField(required=True)
    text = TextField()
    linked_type = TextField(default="post")
    linked_guid = GUIDField()
    height = IntegerField()
    width = IntegerField()
