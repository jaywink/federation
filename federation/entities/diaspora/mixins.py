import logging
import re

from bs4 import BeautifulSoup, Tag
from commonmark import commonmark
from Crypto.PublicKey import RSA
from lxml import etree
from markdownify import markdownify

from federation.entities.diaspora.utils import add_element_to_doc
from federation.entities.mixins import BaseEntity
from federation.entities.utils import get_base_attributes
from federation.exceptions import SignatureVerificationError
from federation.protocols.diaspora.signatures import verify_relayable_signature, create_relayable_signature

logger = logging.getLogger("federation")

class DiasporaEntityMixin(BaseEntity):
    # Normally outbound document is generated from entity. Store one here if at some point we already have a doc
    outbound_doc = None

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


class DiasporaPreSendMixin:
    def pre_send(self):
        # replace media tags with a link to their source since
        # Diaspora instances are likely to filter them out.
        # use the client provided rendered content as source
        try:
            soup = BeautifulSoup(commonmark(self.raw_content, ignore_html_blocks=True), 'html.parser')
            for source in soup.find_all('source', src=re.compile(r'^http')):
                link = Tag(name='a', attrs={'href': source['src']})
                link.string = "{} link: {}".format(source.parent.name, source['src'].split('/')[-1])
                source.parent.replace_with(link)
            self.raw_content = markdownify(str(soup))
        except:
            logger.warning("failed to replace media tags for Diaspora payload.")
                
        # add curly braces to mentions
        if hasattr(self, 'extract_mentions'):
            self.extract_mentions()
        for mention in self._mentions:
            self.raw_content = self.raw_content.replace('@'+mention, '@{'+mention+'}')

            
        

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
