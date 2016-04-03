# -*- coding: utf-8 -*-
from lxml import etree

from federation.entities.base import Comment, Post
from federation.entities.diaspora.utils import format_dt, struct_to_xml


class DiasporaComment(Comment):
    """Diaspora comments additionally have an author_signature."""
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


class DiasporaPost(Post):
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
