import re
from typing import Set

from Crypto.PublicKey import RSA
from lxml import etree

from federation.entities.diaspora.utils import add_element_to_doc
from federation.entities.mixins import BaseEntity
from federation.entities.utils import get_base_attributes
from federation.exceptions import SignatureVerificationError
from federation.protocols.diaspora.signatures import verify_relayable_signature, create_relayable_signature


class DiasporaEntityMixin(BaseEntity):
    # Normally outbound document is generated from entity. Store one here if at some point we already have a doc
    outbound_doc = None

    def extract_mentions(self) -> Set:
        """
        Extract mentions from an entity with ``raw_content``.

        :return: set
        """
        if not hasattr(self, "raw_content"):
            return set()
        mentions = re.findall(r'@{([\S ][^{}]+)}', self.raw_content)
        if not mentions:
            return set()
        _mentions = set()
        for mention in mentions:
            splits = mention.split(";")
            if len(splits) == 1:
                _mentions.add(splits[0].strip(' }'))
            elif len(splits) == 2:
                _mentions.add(splits[1].strip(' }'))
        return _mentions

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

    def sign(self, private_key: RSA) -> None:
        self.signature = create_relayable_signature(private_key, self.to_xml())

    def sign_with_parent(self, private_key):
        if self._source_object:
            doc = etree.fromstring(self._source_object)
        else:
            doc = self.to_xml()
        self.parent_signature = create_relayable_signature(private_key, doc)
        add_element_to_doc(doc, "parent_author_signature", self.parent_signature)
        self.outbound_doc = doc
