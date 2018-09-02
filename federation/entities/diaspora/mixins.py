import re

from lxml import etree

from federation.entities.diaspora.utils import add_element_to_doc
from federation.entities.utils import get_base_attributes
from federation.exceptions import SignatureVerificationError
from federation.protocols.diaspora.signatures import verify_relayable_signature, create_relayable_signature
from federation.utils.diaspora import generate_diaspora_profile_id, parse_diaspora_uri


class DiasporaEntityMixin:
    # Normally outbound document is generated from entity. Store one here if at some point we already have a doc
    outbound_doc = None

    def __init__(self, *args, **kwargs):
        # handle = kwargs.get('handle')
        # guid = kwargs.get('guid')
        # id = kwargs.get('id', '')
        # actor_id = kwargs.get('actor_id', '')
        # if not handle and not guid:
        #     if id.startswith('diaspora://'):
        #         kwargs['handle'], _type, kwargs['guid'] = parse_diaspora_uri(id)
        #     elif actor_id.startswith('diaspora://'):
        #         kwargs['handle'], _type, kwargs['guid'] = parse_diaspora_uri(actor_id)
        #
        # target_handle = kwargs.get('target_handle')
        # target_guid = kwargs.get('target_guid')
        # target_id = kwargs.get('target_id', '')
        # if not target_handle and not target_guid and target_id.startswith('diaspora://'):
        #     kwargs['target_handle'], _type, kwargs['target_guid'] = parse_diaspora_uri(target_id)

        super().__init__(*args, **kwargs)

    def extract_mentions(self):
        """
        Extract mentions from an entity with ``raw_content``.

        :return: set
        """
        if not hasattr(self, "raw_content"):
            return set()
        mentions = re.findall(r'@{[^;]+; [\w.-]+@[^}]+}', self.raw_content)
        if not mentions:
            return set()
        mentions = {s.split(';')[1].strip(' }') for s in mentions}
        mentions = {s for s in mentions}
        return mentions

    def to_string(self) -> str:
        """
        Return string representation of the entity, for debugging mostly.
        """
        return etree.tostring(self.to_xml()).decode('utf-8')

    def to_xml(self):
        """Override in subclasses."""
        raise NotImplementedError

    @classmethod
    def from_base(cls, entity):
        return cls(**get_base_attributes(entity))

    @staticmethod
    def fill_extra_attributes(attributes):
        """Implement in subclasses to fill extra attributes when an XML is transformed to an object.

        This is called just before initializing the entity.

        Args:
            attributes (dict) - Already transformed attributes that will be passed to entity create.

        Returns:
            Must return the attributes dictionary, possibly with changed or additional values.
        """
        return attributes


class DiasporaRelayableMixin(DiasporaEntityMixin):
    _xml_tags = []
    parent_signature = ""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._required += ["signature"]

    def _validate_signatures(self):
        super()._validate_signatures()
        if not self._sender_key:
            raise SignatureVerificationError("Cannot verify entity signature - no sender key available")
        source_doc = etree.fromstring(self._source_object)
        if not verify_relayable_signature(self._sender_key, source_doc, self.signature):
            raise SignatureVerificationError("Signature verification failed.")

    def sign(self, private_key):
        self.signature = create_relayable_signature(private_key, self.to_xml())

    def sign_with_parent(self, private_key):
        if self._source_object:
            doc = etree.fromstring(self._source_object)
        else:
            doc = self.to_xml()
        self.parent_signature = create_relayable_signature(private_key, doc)
        add_element_to_doc(doc, "parent_author_signature", self.parent_signature)
        self.outbound_doc = doc
