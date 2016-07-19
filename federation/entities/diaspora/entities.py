# -*- coding: utf-8 -*-
from lxml import etree

from federation.entities.base import Comment, Post, Reaction, Relationship
from federation.entities.diaspora.utils import format_dt, struct_to_xml, get_base_attributes


class DiasporaEntityMixin(object):
    @classmethod
    def from_base(cls, entity):
        return cls(**get_base_attributes(entity))


class DiasporaComment(DiasporaEntityMixin, Comment):
    """Diaspora comment."""
    author_signature = ""

    def to_xml(self):
        element = etree.Element("comment")
        struct_to_xml(element, [
            {'guid': self.guid},
            {'parent_guid': self.target_guid},
            {'author_signature': self.author_signature},
            {'text': self.raw_content},
            {'diaspora_handle': self.handle},
        ])
        return element


class DiasporaPost(DiasporaEntityMixin, Post):
    """Diaspora post, ie status message."""
    def to_xml(self):
        """Convert to XML message."""
        element = etree.Element("status_message")
        struct_to_xml(element, [
            {'raw_message': self.raw_content},
            {'guid': self.guid},
            {'diaspora_handle': self.handle},
            {'public': 'true' if self.public else 'false'},
            {'created_at': format_dt(self.created_at)}
        ])
        return element


class DiasporaLike(DiasporaEntityMixin, Reaction):
    """Diaspora like."""
    author_signature = ""
    reaction = "like"

    def to_xml(self):
        """Convert to XML message."""
        element = etree.Element("like")
        struct_to_xml(element, [
            {"target_type": "Post"},
            {'guid': self.guid},
            {'parent_guid': self.target_guid},
            {'author_signature': self.author_signature},
            {"positive": "true"},
            {'diaspora_handle': self.handle},
        ])
        return element


class DiasporaRequest(DiasporaEntityMixin, Relationship):
    """Diaspora relationship request."""
    relationship = "sharing"

    def to_xml(self):
        """Convert to XML message."""
        element = etree.Element("request")
        struct_to_xml(element, [
            {"sender_handle": self.handle},
            {"recipient_handle": self.target_handle},
        ])
        return element
