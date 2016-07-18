# -*- coding: utf-8 -*-
from lxml import etree

from federation.entities.diaspora.entities import DiasporaComment, DiasporaPost, DiasporaLike, DiasporaRequest


class TestEntitiesConvertToXML(object):
    def test_post_to_xml(self):
        entity = DiasporaPost(raw_content="raw_content", guid="guid", handle="handle", public=True)
        result = entity.to_xml()
        assert result.tag == "status_message"
        assert len(result.find("created_at").text) > 0
        result.find("created_at").text = ""  # timestamp makes testing painful
        converted = b"<status_message><raw_message>raw_content</raw_message><guid>guid</guid>" \
                    b"<diaspora_handle>handle</diaspora_handle><public>true</public><created_at>" \
                    b"</created_at></status_message>"
        assert etree.tostring(result) == converted

    def test_comment_to_xml(self):
        entity = DiasporaComment(raw_content="raw_content", guid="guid", target_guid="target_guid", handle="handle")
        result = entity.to_xml()
        assert result.tag == "comment"
        converted = b"<comment><guid>guid</guid><parent_guid>target_guid</parent_guid>" \
                    b"<author_signature></author_signature><text>raw_content</text>" \
                    b"<diaspora_handle>handle</diaspora_handle></comment>"
        assert etree.tostring(result) == converted

    def test_like_to_xml(self):
        entity = DiasporaLike(guid="guid", target_guid="target_guid", handle="handle")
        result = entity.to_xml()
        assert result.tag == "like"
        converted = b"<like><target_type>Post</target_type><guid>guid</guid><parent_guid>target_guid</parent_guid>" \
                    b"<author_signature></author_signature><positive>true</positive>" \
                    b"<diaspora_handle>handle</diaspora_handle></like>"
        assert etree.tostring(result) == converted

    def test_request_to_xml(self):
        entity = DiasporaRequest(handle="bob@example.com", target_handle="alice@example.com", relationship="following")
        result = entity.to_xml()
        assert result.tag == "request"
        converted = b"<request><sender_handle>bob@example.com</sender_handle>" \
                    b"<recipient_handle>alice@example.com</recipient_handle></request>"
        assert etree.tostring(result) == converted
