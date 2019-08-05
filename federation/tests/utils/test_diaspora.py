from unittest.mock import patch, Mock, call
from urllib.parse import quote

import pytest
from lxml import html

from federation.entities.base import Profile
from federation.hostmeta.generators import DiasporaHostMeta, generate_hcard
from federation.tests.fixtures.payloads import DIASPORA_PUBLIC_PAYLOAD, DIASPORA_WEBFINGER_JSON, DIASPORA_WEBFINGER
from federation.types import RequestType
# noinspection PyProtectedMember
from federation.utils.diaspora import (
    retrieve_diaspora_hcard, retrieve_diaspora_host_meta, _get_element_text_or_none,
    _get_element_attr_or_none, parse_profile_from_hcard, retrieve_and_parse_profile, retrieve_and_parse_content,
    get_fetch_content_endpoint, fetch_public_key,
    retrieve_and_parse_diaspora_webfinger, parse_diaspora_webfinger, get_public_endpoint, get_private_endpoint)


class TestParseDiasporaWebfinger:
    def test_json_webfinger_is_parsed(self):
        result = parse_diaspora_webfinger(DIASPORA_WEBFINGER_JSON)
        assert result == {"hcard_url": "https://example.org/hcard/users/7dba7ca01d64013485eb3131731751e9"}

    def test_xml_webfinger_is_parsed(self):
        result = parse_diaspora_webfinger(DIASPORA_WEBFINGER)
        assert result == {"hcard_url": "https://server.example/hcard/users/0123456789abcdef"}

    def test_returns_default_if_parsing_fails(self):
        result = parse_diaspora_webfinger("not a valid doc")
        assert result == {"hcard_url": None}


@patch("federation.utils.diaspora.retrieve_and_parse_profile", autospec=True)
def test_fetch_public_key(mock_retrieve):
    mock_retrieve.return_value = Mock(public_key="public key")
    result = fetch_public_key("spam@eggs")
    mock_retrieve.assert_called_once_with("spam@eggs")
    assert result == "public key"


def test_get_fetch_content_endpoint():
    assert get_fetch_content_endpoint("example.com", "status_message", "1234") == \
           "https://example.com/fetch/status_message/1234"


class TestRetrieveDiasporaHCard:
    @patch("federation.utils.diaspora.retrieve_and_parse_diaspora_webfinger", return_value={
        "hcard_url": "http://localhost",
    })
    def test_retrieve_webfinger_is_called(self, mock_retrieve):
        retrieve_diaspora_hcard("bob@localhost")
        assert mock_retrieve.called_with("bob@localhost")

    @patch("federation.utils.diaspora.fetch_document")
    @patch("federation.utils.diaspora.retrieve_and_parse_diaspora_webfinger", return_value={
        "hcard_url": "http://localhost",
    })
    def test_fetch_document_is_called(self, mock_retrieve, mock_fetch):
        mock_fetch.return_value = "document", None, None
        retrieve_diaspora_hcard("bob@localhost")
        mock_fetch.assert_called_with("http://localhost")

    @patch("federation.utils.diaspora.fetch_document")
    @patch("federation.utils.diaspora.retrieve_and_parse_diaspora_webfinger", return_value={
        "hcard_url": "http://localhost",
    })
    def test_returns_none_on_fetch_document_exception(self, mock_retrieve, mock_fetch):
        mock_fetch.return_value = None, None, ValueError()
        result = retrieve_diaspora_hcard("bob@localhost")
        mock_fetch.assert_called_with("http://localhost")
        assert result is None


class TestRetrieveAndParseDiasporaWebfinger:
    @patch("federation.utils.diaspora.retrieve_diaspora_host_meta", return_value=None)
    def test_retrieve_host_meta_is_called(self, mock_retrieve):
        retrieve_and_parse_diaspora_webfinger("bob@localhost")
        mock_retrieve.assert_called_with("localhost")

    @patch("federation.utils.diaspora.fetch_document", return_value=(None, None, None))
    @patch("federation.utils.diaspora.retrieve_diaspora_host_meta", return_value=None)
    def test_fetch_document_is_called__to_fetch_json_webfinger(self, mock_retrieve, mock_fetch):
        retrieve_and_parse_diaspora_webfinger("bob@localhost")
        mock_fetch.assert_called_once_with(
            host="localhost",
            path="/.well-known/webfinger?resource=acct:bob%40localhost",
        )

    @patch("federation.utils.diaspora.XRD.parse_xrd")
    @patch("federation.utils.diaspora.fetch_document", return_value=(None, None, None))
    @patch("federation.utils.diaspora.parse_diaspora_webfinger", return_value={'hcard_url': None})
    @patch("federation.utils.diaspora.retrieve_diaspora_host_meta", return_value=None)
    def test_fetch_document_is_called__to_fetch_xml_webfinger(self, mock_retrieve, mock_parse, mock_fetch, mock_xrd):
        mock_retrieve.return_value = DiasporaHostMeta(
            webfinger_host="https://localhost"
        ).xrd
        mock_xrd.return_value = "document"
        result = retrieve_and_parse_diaspora_webfinger("bob@localhost")
        calls = [
            call(
                host="localhost",
                path="/.well-known/webfinger?resource=acct:bob%40localhost",
            ),
            call("https://localhost/webfinger?q=%s" % quote("bob@localhost")),
        ]
        assert calls == mock_fetch.call_args_list
        assert result == {'hcard_url': None}


class TestRetrieveDiasporaHostMeta:
    @patch("federation.utils.diaspora.XRD.parse_xrd")
    @patch("federation.utils.diaspora.fetch_document")
    def test_fetch_document_is_called(self, mock_fetch, mock_xrd):
        mock_fetch.return_value = "document", None, None
        mock_xrd.return_value = "document"
        document = retrieve_diaspora_host_meta("localhost")
        mock_fetch.assert_called_with(host="localhost", path="/.well-known/host-meta")
        assert document == "document"

    @patch("federation.utils.diaspora.fetch_document")
    def test_returns_none_on_fetch_document_exception(self, mock_fetch):
        mock_fetch.return_value = None, None, ValueError()
        document = retrieve_diaspora_host_meta("localhost")
        mock_fetch.assert_called_with(host="localhost", path="/.well-known/host-meta")
        assert document is None


class TestRetrieveAndParseContent:
    @patch("federation.utils.diaspora.fetch_document", return_value=(None, 404, None))
    @patch("federation.utils.diaspora.get_fetch_content_endpoint", return_value="https://example.com/fetch/spam/eggs")
    def test_calls_fetch_document(self, mock_get, mock_fetch):
        retrieve_and_parse_content(id="eggs", guid="eggs", handle="user@example.com", entity_type="spam")
        mock_fetch.assert_called_once_with("https://example.com/fetch/spam/eggs")

    @patch("federation.utils.diaspora.fetch_document", return_value=(None, 404, None))
    @patch("federation.utils.diaspora.get_fetch_content_endpoint")
    def test_calls_get_fetch_content_endpoint(self, mock_get, mock_fetch):
        retrieve_and_parse_content(id="eggs", guid="eggs", handle="user@example.com", entity_type="spam")
        mock_get.assert_called_once_with("example.com", "spam", "eggs")
        mock_get.reset_mock()
        retrieve_and_parse_content(id="eggs", guid="eggs@spam", handle="user@example.com", entity_type="spam")
        mock_get.assert_called_once_with("example.com", "spam", "eggs@spam")

    @patch("federation.utils.diaspora.fetch_document", return_value=(DIASPORA_PUBLIC_PAYLOAD, 200, None))
    @patch("federation.utils.diaspora.get_fetch_content_endpoint", return_value="https://example.com/fetch/spam/eggs")
    @patch("federation.utils.diaspora.handle_receive", return_value=("sender", "protocol", ["entity"]))
    def test_calls_handle_receive(self, mock_handle, mock_get, mock_fetch):
        entity = retrieve_and_parse_content(
            id="eggs", guid="eggs", handle="user@example.com", entity_type="spam", sender_key_fetcher=sum,
        )
        mock_handle.assert_called_once_with(RequestType(body=DIASPORA_PUBLIC_PAYLOAD), sender_key_fetcher=sum)
        assert entity == "entity"

    @patch("federation.utils.diaspora.fetch_document", return_value=(None, None, Exception()))
    @patch("federation.utils.diaspora.get_fetch_content_endpoint", return_value="https://example.com/fetch/spam/eggs")
    def test_raises_on_fetch_error(self, mock_get, mock_fetch):
        with pytest.raises(Exception):
            retrieve_and_parse_content(id="eggs", guid="eggs", handle="user@example.com", entity_type="spam")

    @patch("federation.utils.diaspora.fetch_document", return_value=(None, 404, None))
    @patch("federation.utils.diaspora.get_fetch_content_endpoint", return_value="https://example.com/fetch/spam/eggs")
    def test_returns_on_404(self, mock_get, mock_fetch):
        result = retrieve_and_parse_content(id="eggs", guid="eggs", handle="user@example.com", entity_type="spam")
        assert not result


class TestGetElementTextOrNone:
    doc = html.fromstring("<foo>bar</foo>")

    def test_text_returned_on_element(self):
        assert _get_element_text_or_none(self.doc, "foo") == "bar"

    def test_none_returned_on_no_element(self):
        assert _get_element_text_or_none(self.doc, "bar") == None


class TestGetElementAttrOrNone:
    doc = html.fromstring("<foo src='baz'>bar</foo>")

    def test_attr_returned_on_attr(self):
        assert _get_element_attr_or_none(self.doc, "foo", "src") == "baz"

    def test_none_returned_on_attr(self):
        assert _get_element_attr_or_none(self.doc, "foo", "href") == None

    def test_none_returned_on_no_element(self):
        assert _get_element_attr_or_none(self.doc, "bar", "href") == None


class TestParseProfileFromHCard:
    def test_profile_is_parsed(self):
        hcard = generate_hcard(
            "diaspora",
            hostname="https://example.com",
            fullname="fullname",
            firstname="firstname",
            lastname="lastname",
            photo300="photo300",
            photo100="photo100",
            photo50="photo50",
            searchable="true",
            guid="guidguidguidguid",
            public_key="public_key",
            username="username",
        )
        profile = parse_profile_from_hcard(hcard, "username@example.com")
        assert profile.name == "fullname"
        assert profile.image_urls == {
            "small": "photo50", "medium": "photo100", "large": "photo300"
        }
        assert profile.public == True
        assert profile.handle == "username@example.com"
        assert profile.guid == "guidguidguidguid"
        assert profile.public_key == "public_key\n"
        profile.validate()


class TestRetrieveAndParseProfile:
    @patch("federation.utils.diaspora.retrieve_diaspora_hcard", return_value=None)
    def test_retrieve_diaspora_hcard_is_called(self, mock_retrieve):
        retrieve_and_parse_profile("foo@bar")
        mock_retrieve.assert_called_with("foo@bar")

    @patch("federation.utils.diaspora.parse_profile_from_hcard")
    @patch("federation.utils.diaspora.retrieve_diaspora_hcard")
    def test_parse_profile_from_hcard_called(self, mock_retrieve, mock_parse):
        hcard = generate_hcard(
            "diaspora",
            hostname="https://hostname",
            fullname="fullname",
            firstname="firstname",
            lastname="lastname",
            photo300="photo300",
            photo100="photo100",
            photo50="photo50",
            searchable="true",
            guid="guid",
            public_key="public_key",
            username="username",
        )
        mock_retrieve.return_value = hcard
        retrieve_and_parse_profile("foo@bar")
        mock_parse.assert_called_with(hcard, "foo@bar")

    @patch("federation.utils.diaspora.parse_profile_from_hcard")
    @patch("federation.utils.diaspora.retrieve_diaspora_hcard")
    def test_profile_that_doesnt_validate_returns_none(self, mock_retrieve, mock_parse):
        hcard = generate_hcard(
            "diaspora",
            hostname="https://hostname",
            fullname="fullname",
            firstname="firstname",
            lastname="lastname",
            photo300="photo300",
            photo100="photo100",
            photo50="photo50",
            searchable="true",
            guid="guid",
            public_key="public_key",
            username="username",
        )
        mock_retrieve.return_value = hcard
        mock_parse.return_value = Profile(guid="123")
        profile = retrieve_and_parse_profile("foo@bar")
        assert profile == None

    @patch("federation.utils.diaspora.parse_profile_from_hcard")
    @patch("federation.utils.diaspora.retrieve_diaspora_hcard")
    def test_profile_validate_is_called(self, mock_retrieve, mock_parse):
        hcard = generate_hcard(
            "diaspora",
            hostname="https://hostname",
            fullname="fullname",
            firstname="firstname",
            lastname="lastname",
            photo300="photo300",
            photo100="photo100",
            photo50="photo50",
            searchable="true",
            guid="guid",
            public_key="public_key",
            username="username",
        )
        mock_retrieve.return_value = hcard
        mock_profile = Mock()
        mock_parse.return_value = mock_profile
        retrieve_and_parse_profile("foo@bar")
        assert mock_profile.validate.called


class TestGetPublicEndpoint:
    def test_correct_endpoint(self):
        endpoint = get_public_endpoint("foobar@example.com")
        assert endpoint == "https://example.com/receive/public"


class TestGetPrivateEndpoint:
    def test_correct_endpoint(self):
        endpoint = get_private_endpoint("foobar@example.com", guid="123456")
        assert endpoint == "https://example.com/receive/users/123456"
