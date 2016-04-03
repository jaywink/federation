# -*- coding: utf-8 -*-
from datetime import datetime

from federation.entities.base import Comment, Post
from federation.entities.diaspora.entities import DiasporaPost, DiasporaComment
from federation.entities.diaspora.mappers import message_to_objects
from federation.tests.fixtures.payloads import DIASPORA_POST_SIMPLE, DIASPORA_POST_COMMENT


class TestDiasporaEntityMappersReceive(object):

    def test_message_to_objects_simple_post(self):
        entities = message_to_objects(DIASPORA_POST_SIMPLE)
        assert len(entities) == 1
        post = entities[0]
        assert isinstance(post, DiasporaPost)
        assert isinstance(post, Post)
        assert post.raw_content == "((status message))"
        assert post.guid == "((guid))"
        assert post.handle == "alice@alice.diaspora.example.org"
        assert post.public == False
        assert post.created_at == datetime(2011, 7, 20, 1, 36, 7)

    def test_message_to_objects_comment(self):
        entities = message_to_objects(DIASPORA_POST_COMMENT)
        assert len(entities) == 1
        comment = entities[0]
        assert isinstance(comment, DiasporaComment)
        assert isinstance(comment, Comment)
        assert comment.target_guid == "((parent_guid))"
        assert comment.guid == "((guid))"
        assert comment.handle == "alice@alice.diaspora.example.org"
        assert comment.participation == "comment"
        assert comment.raw_content == "((text))"
