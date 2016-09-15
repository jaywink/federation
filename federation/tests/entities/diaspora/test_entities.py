# -*- coding: utf-8 -*-
from unittest.mock import patch

import pytest
from lxml import etree

from federation.entities.base import Profile
from federation.entities.diaspora.entities import DiasporaComment, DiasporaPost, DiasporaLike, DiasporaRequest, \
    DiasporaProfile


class TestEntitiesConvertToXML(object):
    def test_post_to_xml(self):
        entity = DiasporaPost(
            raw_content="raw_content", guid="guid", handle="handle", public=True,
            provider_display_name="Socialhome"
        )
        result = entity.to_xml()
        assert result.tag == "status_message"
        assert len(result.find("created_at").text) > 0
        result.find("created_at").text = ""  # timestamp makes testing painful
        converted = b"<status_message><raw_message>raw_content</raw_message><guid>guid</guid>" \
                    b"<diaspora_handle>handle</diaspora_handle><public>true</public><created_at>" \
                    b"</created_at><provider_display_name>Socialhome</provider_display_name></status_message>"
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

    def test_profile_to_xml(self):
        entity = DiasporaProfile(
            handle="bob@example.com", raw_content="foobar", name="Bob Bobertson", public=True,
            tag_list=["socialfederation", "federation"], image_urls={
                "large": "urllarge", "medium": "urlmedium", "small": "urlsmall"
            }
        )
        result = entity.to_xml()
        assert result.tag == "profile"
        converted = b"<profile><diaspora_handle>bob@example.com</diaspora_handle>" \
                    b"<first_name>Bob Bobertson</first_name><last_name></last_name><image_url>urllarge</image_url>" \
                    b"<image_url_small>urlsmall</image_url_small><image_url_medium>urlmedium</image_url_medium>" \
                    b"<gender></gender><bio>foobar</bio><location></location><searchable>true</searchable>" \
                    b"<nsfw>false</nsfw><tag_string>#socialfederation #federation</tag_string></profile>"
        assert etree.tostring(result) == converted


class TestDiasporaProfileFillExtraAttributes(object):
    def test_raises_if_no_handle(self):
        attrs = {"foo": "bar"}
        with pytest.raises(ValueError):
            DiasporaProfile.fill_extra_attributes(attrs)

    @patch("federation.entities.diaspora.entities.retrieve_and_parse_profile")
    def test_calls_retrieve_and_parse_profile(self, mock_retrieve):
        mock_retrieve.return_value = Profile(guid="guidguidguidguid")
        attrs = {"handle": "foo"}
        attrs = DiasporaProfile.fill_extra_attributes(attrs)
        assert attrs == {"handle": "foo", "guid": "guidguidguidguid"}
