from unittest.mock import patch, Mock

import pytest
from lxml import etree

from federation.entities.diaspora.entities import DiasporaComment, DiasporaLike, DiasporaRetraction
from federation.entities.diaspora.mappers import message_to_objects
from federation.exceptions import SignatureVerificationError
from federation.tests.fixtures.keys import get_dummy_private_key
from federation.tests.fixtures.payloads import DIASPORA_POST_COMMENT


class TestEntitiesConvertToXML:
    def test_post_to_xml(self, diasporapost):
        result = diasporapost.to_xml()
        assert result.tag == "status_message"
        assert len(result.find("created_at").text) > 0
        result.find("created_at").text = ""  # timestamp makes testing painful
        converted = b"<status_message><text>raw_content</text><guid>guid</guid>" \
                    b"<author>alice@example.com</author><public>true</public><created_at>" \
                    b"</created_at><provider_display_name>Socialhome</provider_display_name></status_message>"
        assert etree.tostring(result) == converted

    def test_post_to_xml__with_activitypub_id(self, diasporapost_activitypub_id):
        result = diasporapost_activitypub_id.to_xml()
        assert result.tag == "status_message"
        assert len(result.find("created_at").text) > 0
        result.find("created_at").text = ""  # timestamp makes testing painful
        converted = b"<status_message><text>raw_content</text><guid>guid</guid>" \
                    b"<author>alice@example.com</author><public>true</public><created_at>" \
                    b"</created_at><provider_display_name>Socialhome</provider_display_name>" \
                    b"<activitypub_id>https://domain.tld/id</activitypub_id></status_message>"
        assert etree.tostring(result) == converted

    def test_comment_to_xml(self, diasporacomment):
        result = diasporacomment.to_xml()
        assert result.tag == "comment"
        assert len(result.find("created_at").text) > 0
        result.find("created_at").text = ""  # timestamp makes testing painful
        converted = b"<comment><guid>guid</guid><parent_guid>target_guid</parent_guid>" \
                    b"<thread_parent_guid>target_guid</thread_parent_guid>" \
                    b"<author_signature>signature</author_signature><parent_author_signature>" \
                    b"</parent_author_signature><text>raw_content</text><author>alice@example.com</author>" \
                    b"<created_at></created_at></comment>"
        assert etree.tostring(result) == converted

    def test_comment_to_xml__with_activitypub_id(self, diasporacomment_activitypub_id):
        result = diasporacomment_activitypub_id.to_xml()
        assert result.tag == "comment"
        assert len(result.find("created_at").text) > 0
        result.find("created_at").text = ""  # timestamp makes testing painful
        converted = b"<comment><guid>guid</guid><parent_guid>target_guid</parent_guid>" \
                    b"<thread_parent_guid>target_guid</thread_parent_guid>" \
                    b"<author_signature>signature</author_signature><parent_author_signature>" \
                    b"</parent_author_signature><text>raw_content</text><author>alice@example.com</author>" \
                    b"<created_at></created_at><activitypub_id>https://domain.tld/id</activitypub_id></comment>"
        assert etree.tostring(result) == converted

    def test_nested_comment_to_xml(self, diasporanestedcomment):
        result = diasporanestedcomment.to_xml()
        assert result.tag == "comment"
        assert len(result.find("created_at").text) > 0
        result.find("created_at").text = ""  # timestamp makes testing painful
        converted = b"<comment><guid>guid</guid><parent_guid>target_guid</parent_guid>" \
                    b"<thread_parent_guid>thread_target_guid</thread_parent_guid>" \
                    b"<author_signature>signature</author_signature><parent_author_signature>" \
                    b"</parent_author_signature><text>raw_content</text><author>alice@example.com</author>" \
                    b"<created_at></created_at></comment>"
        assert etree.tostring(result) == converted

    def test_like_to_xml(self, diasporalike):
        result = diasporalike.to_xml()
        assert result.tag == "like"
        converted = b"<like><parent_type>Post</parent_type><guid>guid</guid><parent_guid>target_guid</parent_guid>" \
                    b"<author_signature>signature</author_signature><parent_author_signature>" \
                    b"</parent_author_signature><positive>true</positive><author>alice@example.com</author>" \
                    b"</like>"
        assert etree.tostring(result) == converted

    def test_profile_to_xml(self, diasporaprofile):
        result = diasporaprofile.to_xml()
        assert result.tag == "profile"
        converted = b"<profile><author>alice@example.com</author>" \
                    b"<first_name>Bob Bobertson</first_name><last_name></last_name><image_url>urllarge</image_url>" \
                    b"<image_url_small>urlsmall</image_url_small><image_url_medium>urlmedium</image_url_medium>" \
                    b"<gender></gender><bio>foobar</bio><location></location><searchable>true</searchable>" \
                    b"<nsfw>false</nsfw><tag_string>#socialfederation #federation</tag_string></profile>"
        assert etree.tostring(result) == converted

    def test_profile_to_xml__with_activitypub_id(self, diasporaprofile_activitypub_id):
        result = diasporaprofile_activitypub_id.to_xml()
        assert result.tag == "profile"
        converted = b"<profile><author>alice@example.com</author>" \
                    b"<first_name>Bob Bobertson</first_name><last_name></last_name><image_url>urllarge</image_url>" \
                    b"<image_url_small>urlsmall</image_url_small><image_url_medium>urlmedium</image_url_medium>" \
                    b"<gender></gender><bio>foobar</bio><location></location><searchable>true</searchable>" \
                    b"<nsfw>false</nsfw><tag_string>#socialfederation #federation</tag_string>" \
                    b"<activitypub_id>http://example.com/alice</activitypub_id></profile>"
        assert etree.tostring(result) == converted

    def test_retraction_to_xml(self, diasporaretraction):
        result = diasporaretraction.to_xml()
        assert result.tag == "retraction"
        converted = b"<retraction><author>alice@example.com</author>" \
                    b"<target_guid>target_guid</target_guid><target_type>Post</target_type></retraction>"
        assert etree.tostring(result) == converted

    def test_contact_to_xml(self, diasporacontact):
        result = diasporacontact.to_xml()
        assert result.tag == "contact"
        converted = b"<contact><author>alice@example.com</author><recipient>bob@example.org</recipient>" \
                    b"<following>true</following><sharing>true</sharing></contact>"
        assert etree.tostring(result) == converted

    def test_reshare_to_xml(self, diasporareshare):
        result = diasporareshare.to_xml()
        assert result.tag == "reshare"
        result.find("created_at").text = ""  # timestamp makes testing painful
        converted = "<reshare><author>%s</author><guid>%s</guid><created_at></created_at><root_author>%s" \
                    "</root_author><root_guid>%s</root_guid><provider_display_name>%s</provider_display_name>" \
                    "<public>%s</public><text>%s</text><entity_type>%s</entity_type></reshare>" % (
                        diasporareshare.handle, diasporareshare.guid, diasporareshare.target_handle,
                        diasporareshare.target_guid, diasporareshare.provider_display_name,
                        "true" if diasporareshare.public else "false", diasporareshare.raw_content,
                        diasporareshare.entity_type,
                    )
        assert etree.tostring(result).decode("utf-8") == converted


class TestEntitiesExtractMentions:
    def test_extract_mentions__empty_set_if_no_mentions(self, diasporacomment):
        diasporacomment.extract_mentions()
        assert diasporacomment._mentions == set()

    def test_extract_mentions__set_contains_mentioned_handles(self, diasporapost):
        diasporapost.raw_content = 'yeye @{Jason Robinson 🐍🍻; jaywink@jasonrobinson.me} foobar ' \
                                   '@{bar; foo@example.com}'
        diasporapost.extract_mentions()
        assert diasporapost._mentions == {
            'jaywink@jasonrobinson.me',
            'foo@example.com',
        }

    def test_extract_mentions__set_contains_mentioned_handles__without_display_name(self, diasporapost):
        diasporapost.raw_content = 'yeye @{jaywink@jasonrobinson.me} foobar ' \
                                   '@{bar; foo@example.com}'
        diasporapost.extract_mentions()
        assert diasporapost._mentions == {
            'jaywink@jasonrobinson.me',
            'foo@example.com',
        }


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
            raw_content="raw_content",
            created_at="created_at",
            actor_id="handle",
            handle="handle",
            id="guid",
            guid="guid",
            target_id="target_guid",
            target_guid="target_guid",
            root_target_id="target_guid",
            root_target_guid="target_guid",
        )
        entity.sign(get_dummy_private_key())
        assert entity.signature == "XZYggFdQHOicguZ0ReVJkYiK5othHgBgAtwnSmm4NR31qeLa76Ur/i2B5Xi9dtopDlNS8EbFy+MLJ1ds" \
                                   "ovDjPsVC1nLZrL57y0v+HtwJas6hQqNbvmEyr1q6X+0p1i93eINzt/7bxcP5uEGxy8J4ItsJzbDVLlC5" \
                                   "3ZtIg7pmhR0ltqNqBHrgL8WDokfGKFlXqANchbD+Xeyv2COGbI78LwplVdYjHW1+jefjpYhMCxayIvMv" \
                                   "WS8TV1hMTqUz+zSqoCHU04RgjjGW8e8vINDblQwMfEMeJ5T6OP5RiU3zCqDc3uL2zxHHh9IGC+clVuhP" \
                                   "HTv8tHUHNLgc2vIzRtGh6w=="

    def test_signing_like_works(self):
        entity = DiasporaLike(
            actor_id="handle",
            handle="handle",
            id="guid",
            guid="guid",
            target_id="target_guid",
            target_guid="target_guid",
        )
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
    def test_sign_with_parent__calls_to_xml(self, mock_validate):
        entity = DiasporaComment()
        with patch.object(entity, "to_xml") as mock_to_xml:
            entity.sign_with_parent(get_dummy_private_key())
            mock_to_xml.assert_called_once_with()


class TestDiasporaRelayableEntityValidate():
    def test_raises_if_no_sender_key(self):
        entity = DiasporaComment()
        with pytest.raises(SignatureVerificationError):
            entity._validate_signatures()

    @patch("federation.entities.diaspora.mixins.verify_relayable_signature")
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
