# -*- coding: utf-8 -*-
from datetime import datetime

import pytest

from federation.entities.base import Comment, Post, Reaction, Relationship
from federation.entities.diaspora.entities import DiasporaPost, DiasporaComment, DiasporaLike, DiasporaRequest
from federation.entities.diaspora.mappers import message_to_objects, get_outbound_entity
from federation.tests.fixtures.payloads import DIASPORA_POST_SIMPLE, DIASPORA_POST_COMMENT, DIASPORA_POST_LIKE, \
    DIASPORA_REQUEST


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

    def test_message_to_objects_like(self):
        entities = message_to_objects(DIASPORA_POST_LIKE)
        assert len(entities) == 1
        like = entities[0]
        assert isinstance(like, DiasporaLike)
        assert isinstance(like, Reaction)
        assert like.target_guid == "((parent_guid))"
        assert like.guid == "((guid))"
        assert like.handle == "alice@alice.diaspora.example.org"
        assert like.participation == "reaction"
        assert like.reaction == "like"

    def test_message_to_objects_request(self):
        entities = message_to_objects(DIASPORA_REQUEST)
        assert len(entities) == 2
        sharing = entities[0]
        assert isinstance(sharing, DiasporaRequest)
        assert isinstance(sharing, Relationship)
        following = entities[1]
        assert not isinstance(following, DiasporaRequest)
        assert isinstance(following, Relationship)
        assert sharing.handle == "bob@example.com"
        assert following.handle == "bob@example.com"
        assert sharing.target_handle == "alice@alice.diaspora.example.org"
        assert following.target_handle == "alice@alice.diaspora.example.org"
        assert sharing.relationship == "sharing"
        assert following.relationship == "following"


class TestGetOutboundEntity(object):
    def test_already_fine_entities_are_returned_as_is(self):
        entity = DiasporaPost()
        assert get_outbound_entity(entity) == entity
        entity = DiasporaLike()
        assert get_outbound_entity(entity) == entity
        entity = DiasporaComment()
        assert get_outbound_entity(entity) == entity
        entity = DiasporaRequest()
        assert get_outbound_entity(entity) == entity

    def test_post_is_converted_to_diasporapost(self):
        entity = Post()
        assert isinstance(get_outbound_entity(entity), DiasporaPost)

    def test_comment_is_converted_to_diasporacomment(self):
        entity = Comment()
        assert isinstance(get_outbound_entity(entity), DiasporaComment)

    def test_reaction_of_like_is_converted_to_diasporaplike(self):
        entity = Reaction(reaction="like")
        assert isinstance(get_outbound_entity(entity), DiasporaLike)

    def test_relationship_of_sharing_or_following_is_converted_to_diasporarequest(self):
        entity = Relationship(relationship="sharing")
        assert isinstance(get_outbound_entity(entity), DiasporaRequest)
        entity = Relationship(relationship="following")
        assert isinstance(get_outbound_entity(entity), DiasporaRequest)

    def test_other_reaction_raises(self):
        entity = Reaction(reaction="foo")
        with pytest.raises(ValueError):
            get_outbound_entity(entity)

    def test_other_relation_raises(self):
        entity = Relationship(relationship="foo")
        with pytest.raises(ValueError):
            get_outbound_entity(entity)
