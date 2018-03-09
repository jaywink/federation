import datetime
import warnings

from dirty_validators.basic import Email

from federation.utils.text import validate_handle

__all__ = (
    "Post", "Image", "Comment", "Reaction", "Relationship", "Profile", "Retraction", "Follow", "Share",
)


class BaseEntity:
    _allowed_children = ()
    # If we have a receiver for a private payload, store receiving user guid here
    _receiving_guid = ""
    _source_protocol = ""
    # Contains the original object from payload as a string
    _source_object = None
    _sender_key = ""
    signature = ""

    def __init__(self, *args, **kwargs):
        self._required = []
        self._children = []
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                warnings.warn("%s.__init__ got parameter %s which this class does not support - ignoring." % (
                    self.__class__.__name__, key
                ))

    @property
    def id(self):
        """Global network ID.

        Future expansion: Convert later into an attribute which with ActivityPub will have the 'id' directly.
        """
        return

    def validate(self):
        """Do validation.

        1) Check `_required` have been given
        2) Make sure all attrs in required have a non-empty value
        3) Loop through attributes and call their `validate_<attr>` methods, if any.
        4) Validate allowed children
        5) Validate signatures
        """
        attributes = []
        validates = []
        # Collect attributes and validation methods
        for attr in dir(self):
            if not attr.startswith("_"):
                attr_type = type(getattr(self, attr))
                if attr_type != "method":
                    if getattr(self, "validate_{attr}".format(attr=attr), None):
                        validates.append(getattr(self, "validate_{attr}".format(attr=attr)))
                    attributes.append(attr)
        self._validate_empty_attributes(attributes)
        self._validate_required(attributes)
        self._validate_attributes(validates)
        self._validate_children()
        self._validate_signatures()

    def _validate_required(self, attributes):
        """Ensure required attributes are present."""
        required_fulfilled = set(self._required).issubset(set(attributes))
        if not required_fulfilled:
            raise ValueError(
                "Not all required attributes fulfilled. Required: {required}".format(required=set(self._required))
            )

    def _validate_attributes(self, validates):
        """Call individual attribute validators."""
        for validator in validates:
            validator()

    def _validate_empty_attributes(self, attributes):
        """Check that required attributes are not empty."""
        attrs_to_check = set(self._required) & set(attributes)
        for attr in attrs_to_check:
            value = getattr(self, attr)  # We should always have a value here
            if value is None or value == "":
                raise ValueError(
                    "Attribute %s cannot be None or an empty string since it is required." % attr
                )

    def _validate_children(self):
        """Check that the children we have are allowed here."""
        for child in self._children:
            if child.__class__ not in self._allowed_children:
                raise ValueError(
                    "Child %s is not allowed as a children for this %s type entity." % (
                        child, self.__class__
                    )
                )

    def _validate_signatures(self):
        """Override in subclasses where necessary"""
        pass

    def sign(self, private_key):
        """Implement in subclasses if needed."""
        pass

    def sign_with_parent(self, private_key):
        """Implement in subclasses if needed."""
        pass


class GUIDMixin(BaseEntity):
    guid = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._required += ["guid"]

    def validate_guid(self):
        if len(self.guid) < 16:
            raise ValueError("GUID must be at least 16 characters")


class TargetGUIDMixin(BaseEntity):
    target_guid = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._required += ["target_guid"]

    @property
    def target_id(self):
        """Global network target ID.

        Future expansion: convert to attribute when ActivityPub is supported.
        """
        return

    def validate_target_guid(self):
        if len(self.target_guid) < 16:
            raise ValueError("Target GUID must be at least 16 characters")


class ParticipationMixin(TargetGUIDMixin):
    """Reflects a participation to something."""
    participation = ""

    _participation_valid_values = ["reaction", "subscription", "comment"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._required += ["participation"]

    def validate_participation(self):
        """Ensure participation is of a certain type."""
        if self.participation not in self._participation_valid_values:
            raise ValueError("participation should be one of: {valid}".format(
                valid=", ".join(self._participation_valid_values)
            ))


class HandleMixin(BaseEntity):
    handle = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._required += ["handle"]

    def validate_handle(self):
        if not validate_handle(self.handle):
            raise ValueError("Handle is not valid")


class PublicMixin(BaseEntity):
    public = False

    def validate_public(self):
        if not isinstance(self.public, bool):
            raise ValueError("Public is not valid - it should be True or False")


class CreatedAtMixin(BaseEntity):
    created_at = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._required += ["created_at"]
        if not "created_at" in kwargs:
            self.created_at = datetime.datetime.now()


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
        return {word.strip("#").lower() for word in self.raw_content.split() if word.startswith("#") and len(word) > 1}


class OptionalRawContentMixin(RawContentMixin):
    """A version of the RawContentMixin where `raw_content` is not required."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._required.remove("raw_content")


class EntityTypeMixin(BaseEntity):
    """Provides a field for entity type.

    Validates it is one of our entities.
    """
    entity_type = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._required += ["entity_type"]

    def validate_entity_type(self):
        """Ensure type is some entity we know of."""
        if self.entity_type not in __all__:
            raise ValueError("Entity type %s not recognized." % self.entity_type)


class ProviderDisplayNameMixin(BaseEntity):
    """Provides a field for provider display name."""
    provider_display_name = ""


class TargetHandleMixin(BaseEntity):
    """Provides a target handle field."""
    target_handle = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._required += ["target_handle"]

    def validate_target_handle(self):
        if not validate_handle(self.target_handle):
            raise ValueError("Target handle is not valid")


class Image(GUIDMixin, HandleMixin, PublicMixin, OptionalRawContentMixin, CreatedAtMixin):
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


class Post(RawContentMixin, GUIDMixin, HandleMixin, PublicMixin, CreatedAtMixin, ProviderDisplayNameMixin):
    """Reflects a post, status message, etc, which will be composed from the message or to the message."""
    location = ""

    _allowed_children = (Image,)


class Comment(RawContentMixin, GUIDMixin, ParticipationMixin, CreatedAtMixin, HandleMixin):
    """Represents a comment, linked to another object."""
    participation = "comment"

    _allowed_children = (Image,)


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


class Relationship(CreatedAtMixin, HandleMixin, TargetHandleMixin):
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


class Follow(CreatedAtMixin, HandleMixin, TargetHandleMixin):
    """Represents a handle following or unfollowing another handle."""
    following = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._required += ["following"]


class Profile(CreatedAtMixin, HandleMixin, OptionalRawContentMixin, PublicMixin, GUIDMixin):
    """Represents a profile for a user."""
    name = ""
    email = ""
    gender = ""
    location = ""
    nsfw = False
    public_key = ""
    image_urls = None
    tag_list = None

    _allowed_children = (Image,)

    def __init__(self, *args, **kwargs):
        self.image_urls = {
            "small": "", "medium": "", "large": ""
        }
        self.tag_list = []
        super().__init__(*args, **kwargs)

    def validate_email(self):
        if self.email:
            validator = Email()
            if not validator.is_valid(self.email):
                raise ValueError("Email is not valid")


class Retraction(CreatedAtMixin, HandleMixin, TargetGUIDMixin, EntityTypeMixin):
    """Represents a retraction of content by author."""
    pass


class Share(CreatedAtMixin, HandleMixin, TargetGUIDMixin, GUIDMixin, EntityTypeMixin, OptionalRawContentMixin,
            PublicMixin, ProviderDisplayNameMixin, TargetHandleMixin):
    """Represents a share of another entity.

    ``entity_type`` defaults to "Post" but can be any base entity class name. It should be the class name of the
    entity that was shared.

    The optional ``raw_content`` can be used for a "quoted share" case where the sharer adds their own note to the
    share.
    """
    entity_type = "Post"
