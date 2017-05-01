from unittest.mock import patch

import pytest
from lxml import etree

from federation.entities.base import Profile
from federation.entities.diaspora.entities import (
    DiasporaComment, DiasporaPost, DiasporaLike, DiasporaRequest, DiasporaProfile, DiasporaRetraction,
)
from federation.tests.fixtures.keys import get_dummy_private_key


class TestEntitiesConvertToXML():
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
        entity = DiasporaComment(
            raw_content="raw_content", guid="guid", target_guid="target_guid", handle="handle",
            signature="signature"
        )
        result = entity.to_xml()
        assert result.tag == "comment"
        converted = b"<comment><guid>guid</guid><parent_guid>target_guid</parent_guid>" \
                    b"<author_signature>signature</author_signature><text>raw_content</text>" \
                    b"<diaspora_handle>handle</diaspora_handle></comment>"
        assert etree.tostring(result) == converted

    def test_like_to_xml(self):
        entity = DiasporaLike(guid="guid", target_guid="target_guid", handle="handle", signature="signature")
        result = entity.to_xml()
        assert result.tag == "like"
        converted = b"<like><target_type>Post</target_type><guid>guid</guid><parent_guid>target_guid</parent_guid>" \
                    b"<author_signature>signature</author_signature><positive>true</positive>" \
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

    def test_retraction_to_xml(self):
        entity = DiasporaRetraction(handle="bob@example.com", target_guid="x" * 16, entity_type="Post")
        result = entity.to_xml()
        assert result.tag == "retraction"
        converted = b"<retraction><author>bob@example.com</author>" \
                    b"<target_guid>xxxxxxxxxxxxxxxx</target_guid><target_type>Post</target_type></retraction>"
        assert etree.tostring(result) == converted


class TestDiasporaProfileFillExtraAttributes():
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


class TestDiasporaRetractionEntityConverters():
    def test_entity_type_from_remote(self):
        assert DiasporaRetraction.entity_type_from_remote("Post") == "Post"
        assert DiasporaRetraction.entity_type_from_remote("Like") == "Reaction"
        assert DiasporaRetraction.entity_type_from_remote("Photo") == "Image"
        assert DiasporaRetraction.entity_type_from_remote("Comment") == "Comment"

    def test_entity_type_to_remote(self):
        assert DiasporaRetraction.entity_type_to_remote("Post") == "Post"
        assert DiasporaRetraction.entity_type_to_remote("Reaction") == "Like"
        assert DiasporaRetraction.entity_type_to_remote("Image") == "Photo"
        assert DiasporaRetraction.entity_type_to_remote("Comment") == "Comment"


class TestDiasporaRelayableEntitySigning():
    def test_signing_comment_works(self):
        entity = DiasporaComment(
            raw_content="raw_content", guid="guid", target_guid="target_guid", handle="handle",
        )
        entity.sign(get_dummy_private_key())
        assert entity.signature == "f3wkKDEhlT8zThEfaBcuKs4s0MbbWm9XPyx2ivrAg3jBtXQ6lXm5mgi9buwm-QyzxAGnk5Zth6HrYYB-" \
                                   "NoieyoR4j54ryyPMB0gHwUO05tzjAMpvLyDlOyxLYFIl302ib2In9LJ5wa15VaEm9DW2-1WlCK72FonO" \
                                   "oGx0qXDUc-NRn4s_UXBPNgM_Xsz3466AM1y98rUowHnpa0bxDjKcf7HMy4zuJ7XcsJAlofUHXCMX9TOm" \
                                   "SBIwF5MlCkFL28R2cRAzJgNOBLw-a8arfi613bqo1Xq26-2PuFF0ng_OVOQOVFsO60H5wi_49FREWYdG" \
                                   "ZdmHltxf76yWG6R1Zqpvag=="

    def test_signing_like_works(self):
        entity = DiasporaLike(guid="guid", target_guid="target_guid", handle="handle")
        entity.sign(get_dummy_private_key())
        assert entity.signature == "apkcOn6marHfo0rHiOnQq-qqspxxWOJNklQKQjoJUHmXDNRnBp8aPoLKqVOznsTEpEIhM1p5_8mPilgY" \
                                   "yVFHepi_m744DFQByx7hVkMhGFiZWtJx1tTWSl1d7H85FTlE0DyPwiRYVTrG3vQD3Dr-b08WiOEzG-ii" \
                                   "Q0t-vWGl8cgSS0_34mvvqX-HKUdmun2vQ50bPckNLoj3hDI6HcmZ8qFf_xx8y1BbE0zx5rTo7yOlWq8Y" \
                                   "sC28oRHqHpIzOfhkIHyt-hOjO_mpuZLd7qOPfIySnGW6hM1iKewoJVDuVMN5w5VB46ETRum8JpvTQO8i" \
                                   "DPB-ZqbqcEasfm2CQIxVLA=="
