from unittest.mock import patch, Mock

import pytest
from lxml import etree

from federation.entities.base import Profile
from federation.entities.diaspora.entities import (
    DiasporaComment, DiasporaPost, DiasporaLike, DiasporaRequest, DiasporaProfile, DiasporaRetraction,
    DiasporaContact, DiasporaReshare)
from federation.entities.diaspora.mappers import message_to_objects
from federation.exceptions import SignatureVerificationError
from federation.tests.factories.entities import ShareFactory
from federation.tests.fixtures.keys import get_dummy_private_key
from federation.tests.fixtures.payloads import DIASPORA_POST_COMMENT


class TestEntitiesConvertToXML:
    def test_post_to_xml(self):
        entity = DiasporaPost(
            raw_content="raw_content", guid="guid", handle="handle", public=True,
            provider_display_name="Socialhome"
        )
        result = entity.to_xml()
        assert result.tag == "status_message"
        assert len(result.find("created_at").text) > 0
        result.find("created_at").text = ""  # timestamp makes testing painful
        converted = b"<status_message><text>raw_content</text><guid>guid</guid>" \
                    b"<author>handle</author><public>true</public><created_at>" \
                    b"</created_at><provider_display_name>Socialhome</provider_display_name></status_message>"
        assert etree.tostring(result) == converted

    def test_comment_to_xml(self):
        entity = DiasporaComment(
            raw_content="raw_content", guid="guid", target_guid="target_guid", handle="handle",
            signature="signature"
        )
        result = entity.to_xml()
        assert result.tag == "comment"
        assert len(result.find("created_at").text) > 0
        result.find("created_at").text = ""  # timestamp makes testing painful
        converted = b"<comment><guid>guid</guid><parent_guid>target_guid</parent_guid>" \
                    b"<author_signature>signature</author_signature><parent_author_signature>" \
                    b"</parent_author_signature><text>raw_content</text><author>handle</author>" \
                    b"<created_at></created_at></comment>"
        assert etree.tostring(result) == converted

    def test_like_to_xml(self):
        entity = DiasporaLike(guid="guid", target_guid="target_guid", handle="handle", signature="signature")
        result = entity.to_xml()
        assert result.tag == "like"
        converted = b"<like><parent_type>Post</parent_type><guid>guid</guid><parent_guid>target_guid</parent_guid>" \
                    b"<author_signature>signature</author_signature><parent_author_signature>" \
                    b"</parent_author_signature><positive>true</positive><author>handle</author>" \
                    b"</like>"
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
        converted = b"<profile><author>bob@example.com</author>" \
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

    def test_contact_to_xml(self):
        entity = DiasporaContact(handle="alice@example.com", target_handle="bob@example.org", following=True)
        result = entity.to_xml()
        assert result.tag == "contact"
        converted = b"<contact><author>alice@example.com</author><recipient>bob@example.org</recipient>" \
                    b"<following>true</following><sharing>true</sharing></contact>"
        assert etree.tostring(result) == converted

    def test_reshare_to_xml(self):
        base_entity = ShareFactory()
        entity = DiasporaReshare.from_base(base_entity)
        result = entity.to_xml()
        assert result.tag == "reshare"
        result.find("created_at").text = ""  # timestamp makes testing painful
        converted = "<reshare><author>%s</author><guid>%s</guid><created_at></created_at><root_author>%s" \
                    "</root_author><root_guid>%s</root_guid><provider_display_name>%s</provider_display_name>" \
                    "<public>%s</public><text>%s</text><entity_type>%s</entity_type></reshare>" % (
                        entity.handle, entity.guid, entity.target_handle, entity.target_guid,
                        entity.provider_display_name, "true" if entity.public else "false", entity.raw_content,
                        entity.entity_type,
                    )
        assert etree.tostring(result).decode("utf-8") == converted


class TestEntityAttributes:
    def test_comment_ids(self, diasporacomment):
        assert diasporacomment.id == "diaspora://handle/comment/guid"
        assert not diasporacomment.target_id

    def test_contact_ids(self, diasporacontact):
        assert not diasporacontact.id
        assert not diasporacontact.target_id

    def test_like_ids(self, diasporalike):
        assert diasporalike.id == "diaspora://handle/like/guid"
        assert not diasporalike.target_id

    def test_post_ids(self, diasporapost):
        assert diasporapost.id == "diaspora://handle/status_message/guid"
        assert not diasporapost.target_id

    def test_profile_ids(self, diasporaprofile):
        assert diasporaprofile.id == "diaspora://bob@example.com/profile/"
        assert not diasporaprofile.target_id

    def test_request_ids(self, diasporarequest):
        assert not diasporarequest.id
        assert not diasporarequest.target_id

    def test_reshare_ids(self, diasporareshare):
        assert diasporareshare.id == "diaspora://%s/reshare/%s" % (diasporareshare.handle, diasporareshare.guid)
        assert diasporareshare.target_id == "diaspora://%s/status_message/%s" % (
            diasporareshare.target_handle, diasporareshare.target_guid
        )

    def test_retraction_ids(self, diasporaretraction):
        assert not diasporaretraction.id
        assert not diasporaretraction.target_id


class TestDiasporaProfileFillExtraAttributes:
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


class TestDiasporaRetractionEntityConverters:
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


class TestDiasporaRelayableMixin:
    @patch("federation.entities.diaspora.entities.format_dt", side_effect=lambda v: v)
    def test_signing_comment_works(self, mock_format_dt):
        entity = DiasporaComment(
            raw_content="raw_content", guid="guid", target_guid="target_guid", handle="handle",
            created_at="created_at",
        )
        entity.sign(get_dummy_private_key())
        assert entity.signature == "OWvW/Yxw4uCnx0WDn0n5/B4uhyZ8Pr6h3FZaw8J7PCXyPluOfYXFoHO21bykP8c2aVnuJNHe+lmeAkUC" \
                                   "/kHnl4yxk/jqe3uroW842OWvsyDRQ11vHxhIqNMjiepFPkZmXX3vqrYYh5FrC/tUsZrEc8hHoOIHXFR2" \
                                   "kGD0gPV+4EEG6pbMNNZ+SBVun0hvruX8iKQVnBdc/+zUI9+T/MZmLyqTq/CvuPxDyHzQPSHi68N9rJyr" \
                                   "4Xa1K+R33Xq8eHHxs8LVNRqzaHGeD3DX8yBu/vP9TYmZsiWlymbuGwLCa4Yfv/VS1hQZovhg6YTxV4CR" \
                                   "v4ToGL+CAJ7UHEugRRBwDw=="

    def test_signing_like_works(self):
        entity = DiasporaLike(guid="guid", target_guid="target_guid", handle="handle")
        entity.sign(get_dummy_private_key())
        assert entity.signature == "apkcOn6marHfo0rHiOnQq+qqspxxWOJNklQKQjoJUHmXDNRnBp8aPoLKqVOznsTEpEIhM1p5/8mPilgY" \
                                   "yVFHepi/m744DFQByx7hVkMhGFiZWtJx1tTWSl1d7H85FTlE0DyPwiRYVTrG3vQD3Dr+b08WiOEzG+ii" \
                                   "Q0t+vWGl8cgSS0/34mvvqX+HKUdmun2vQ50bPckNLoj3hDI6HcmZ8qFf/xx8y1BbE0zx5rTo7yOlWq8Y" \
                                   "sC28oRHqHpIzOfhkIHyt+hOjO/mpuZLd7qOPfIySnGW6hM1iKewoJVDuVMN5w5VB46ETRum8JpvTQO8i" \
                                   "DPB+ZqbqcEasfm2CQIxVLA=="

    @patch("federation.entities.diaspora.mappers.DiasporaComment._validate_signatures")
    def test_sign_with_parent(self, mock_validate):
        entities = message_to_objects(DIASPORA_POST_COMMENT, "alice@alice.diaspora.example.org",
                                      sender_key_fetcher=Mock())
        entity = entities[0]
        entity.sign_with_parent(get_dummy_private_key())
        assert entity.parent_signature == "UTIDiFZqjxfU6ssVlmjz2RwOD/WPmMTFv57qOm0BZvBhF8Ef49Ynse1c2XTtx3rs8DyRMn54" \
                                          "Uw4E0T+3t0Q5SHEQTLtRnOdRXrgNGAnlJ2xRmBWqe6xvvgc4nJ8OnffXhVgI8DBx6YUFRDjJ" \
                                          "fnVQhnqbWr4ZAcpywCyL9IDkap3cTyn6wHo2WFRtq5syTCtMS8RZLXgpVLCeMfHhrXlePIA/" \
                                          "YwMNn0GGi+9qSWXYVFG75cPjcWeY4t5q8EHCQReSSxG4a3HGbc7MigLvHzuhdOWOV8563dYo" \
                                          "/5xS3zlQUt8I3AwXOzHr+57r1egMBHYyXTXsS8gFisj7mH4TsLM+Yw=="
        assert etree.tostring(entity.outbound_doc) == b'<comment>\n      <guid>((guidguidguidguidguidguid))</guid>\n' \
                                                      b'      <parent_guid>((parent_guidparent_guidparent_guidparent' \
                                                      b'_guid))</parent_guid>\n      <author_signature>((base64-enco' \
                                                      b'ded data))</author_signature>\n      <text>((text))</text>\n' \
                                                      b'      <author>alice@alice.diaspora.example.org</author>\n   ' \
                                                      b'   <author_signature>((signature))</author_signature>\n    ' \
                                                      b'<parent_author_signature>UTIDiFZqjxfU6ssVlmjz2RwOD/WPmMTFv57' \
                                                      b'qOm0BZvBhF8Ef49Ynse1c2XTtx3rs8DyRMn54Uw4E0T+3t0Q5SHEQTLtRnOd' \
                                                      b'RXrgNGAnlJ2xRmBWqe6xvvgc4nJ8OnffXhVgI8DBx6YUFRDjJfnVQhnqbWr4' \
                                                      b'ZAcpywCyL9IDkap3cTyn6wHo2WFRtq5syTCtMS8RZLXgpVLCeMfHhrXlePIA' \
                                                      b'/YwMNn0GGi+9qSWXYVFG75cPjcWeY4t5q8EHCQReSSxG4a3HGbc7MigLvHzu' \
                                                      b'hdOWOV8563dYo/5xS3zlQUt8I3AwXOzHr+57r1egMBHYyXTXsS8gFisj7mH4' \
                                                      b'TsLM+Yw==</parent_author_signature></comment>'

    @patch("federation.entities.diaspora.mappers.DiasporaComment._validate_signatures")
    def test_sign_with_parent(self, mock_validate):
        entity = DiasporaComment()
        with patch.object(entity, "to_xml") as mock_to_xml:
            entity.sign_with_parent(get_dummy_private_key())
            mock_to_xml.assert_called_once_with()


class TestDiasporaRelayableEntityValidate():
    def test_raises_if_no_sender_key(self):
        entity = DiasporaComment()
        with pytest.raises(SignatureVerificationError):
            entity._validate_signatures()

    @patch("federation.entities.diaspora.entities.verify_relayable_signature")
    def test_calls_verify_signature(self, mock_verify):
        entity = DiasporaComment()
        entity._sender_key = "key"
        entity._source_object = "<obj></obj>"
        entity.signature = "sig"
        mock_verify.return_value = False
        with pytest.raises(SignatureVerificationError):
            entity._validate_signatures()
        mock_verify.reset_mock()
        mock_verify.return_value = True
        entity._validate_signatures()
