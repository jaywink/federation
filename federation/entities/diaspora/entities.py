# -*- coding: utf-8 -*-
from ..base import Comment


class DiasporaComment(Comment):
    """Diaspora comments additionally have an author_signature."""
    @property
    def author_signature(self):
        #TODO: implement at later stage when outbound payloads are to be used
        return ""
