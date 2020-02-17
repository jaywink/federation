import datetime
import importlib
import re
import warnings
from typing import List, Set, Union, Dict

from commonmark import commonmark

from federation.entities.activitypub.enums import ActivityType
from federation.entities.utils import get_name_for_profile
from federation.utils.text import process_text_links, find_tags


class BaseEntity:
    _allowed_children: tuple = ()
    _children: List = None
    _mentions: Set = None
    _receivers: List = None
    _source_protocol: str = ""
    # Contains the original object from payload as a string
    _source_object: Union[str, Dict] = None
    _sender_key: str = ""
    # ActivityType
    activity: ActivityType = None
    activity_id: str = ""
    actor_id: str = ""
    # Server base url
    base_url: str = ""
    guid: str = ""
    handle: str = ""
    id: str = ""
    signature: str = ""

    def __init__(self, *args, **kwargs):
        self._required = ["id", "actor_id"]
        self._children = []
        self._mentions = set()
        self._receivers = []
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                warnings.warn("%s.__init__ got parameter %s which this class does not support - ignoring." % (
                    self.__class__.__name__, key
                ))
        if not self.activity:
            # Fill a default activity if not given and type of entity class has one
            self.activity = getattr(self, "_default_activity", None)

    def as_protocol(self, protocol):
        entities = importlib.import_module(f"federation.entities.{protocol}.entities")
        klass = getattr(entities, f"{protocol.title()}{self.__class__.__name__}")
        return klass.from_base(self)

    def post_receive(self):
        """
        Run any actions after deserializing the payload into an entity.
        """
        pass

    def pre_send(self):
        """
        Run any actions before serializing the entity for sending.
        """
        pass

    def validate(self, direction: str = "inbound") -> None:
        """Do validation.

        1) Check `_required` have been given
        2) Make sure all attrs in required have a non-empty value
        3) Loop through attributes and call their `validate_<attr>` methods, if any.
        4) Validate allowed children
        5) Validate signatures (if inbound)
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
        if direction == "inbound":
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
            if not isinstance(child, self._allowed_children):
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


class PublicMixin(BaseEntity):
    public = False

    def validate_public(self):
        if not isinstance(self.public, bool):
            raise ValueError("Public is not valid - it should be True or False")


class TargetIDMixin(BaseEntity):
    target_id = ""
    target_handle = ""
    target_guid = ""

    def validate(self, *args, **kwargs) -> None:
        super().validate(*args, **kwargs)
        # Ensure one of the target attributes is filled at least
        if not self.target_id and not self.target_handle and not self.target_guid:
            raise ValueError("Must give one of the target attributes for TargetIDMixin.")


class RootTargetIDMixin(BaseEntity):
    root_target_id = ""
    root_target_handle = ""
    root_target_guid = ""


class ParticipationMixin(TargetIDMixin):
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


class CreatedAtMixin(BaseEntity):
    created_at = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._required += ["created_at"]
        if not "created_at" in kwargs:
            self.created_at = datetime.datetime.now()


class RawContentMixin(BaseEntity):
    _media_type: str = "text/markdown"
    _mentions: Set = None
    _rendered_content: str = ""
    raw_content: str = ""

    def __init__(self, *args, **kwargs):
        self._mentions = set()
        super().__init__(*args, **kwargs)
        self._required += ["raw_content"]

    @property
    def rendered_content(self) -> str:
        """Returns the rendered version of raw_content, or just raw_content."""
        if self._rendered_content:
            return self._rendered_content
        elif self._media_type == "text/markdown" and self.raw_content:
            rendered = commonmark(self.raw_content).strip()
            if self._mentions:
                for mention in self._mentions:
                    # Only linkify mentions that are URL's
                    if not mention.startswith("http"):
                        continue
                    display_name = get_name_for_profile(mention)
                    if not display_name:
                        display_name = mention
                    rendered = rendered.replace(
                        "@{%s}" % mention,
                        f'@<a href="{mention}" class="mention">{display_name}</a>',
                    )
            # Finally linkify remaining URL's that are not links
            rendered = process_text_links(rendered)
            return rendered
        return self.raw_content

    @property
    def tags(self) -> List[str]:
        """Returns a `list` of unique tags contained in `raw_content`."""
        if not self.raw_content:
            return []
        tags = find_tags(self.raw_content)
        return sorted(tags)

    def extract_mentions(self):
        matches = re.findall(r'@{([\S ][^{}]+)}', self.raw_content)
        if not matches:
            return
        for mention in matches:
            splits = mention.split(";")
            if len(splits) == 1:
                self._mentions.add(splits[0].strip(' }'))
            elif len(splits) == 2:
                self._mentions.add(splits[1].strip(' }'))


class OptionalRawContentMixin(RawContentMixin):
    """A version of the RawContentMixin where `raw_content` is not required."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._required.remove("raw_content")


class EntityTypeMixin(BaseEntity):
    """
    Provides a field for entity type.
    """
    entity_type = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._required += ["entity_type"]


class ProviderDisplayNameMixin(BaseEntity):
    """Provides a field for provider display name."""
    provider_display_name = ""
