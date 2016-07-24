# -*- coding: utf-8 -*-
from unittest.mock import patch
from urllib.parse import quote

from lxml import html

from federation.hostmeta.generators import DiasporaWebFinger, DiasporaHostMeta, DiasporaHCard, generate_hcard
from federation.utils.diaspora import retrieve_diaspora_hcard, retrieve_diaspora_webfinger, retrieve_diaspora_host_meta, \
    _get_element_text_or_none, _get_element_attr_or_none, parse_profile_from_hcard, retrieve_and_parse_profile


class TestRetrieveDiasporaHCard(object):
    @patch("federation.utils.diaspora.retrieve_diaspora_webfinger", return_value=None)
    def test_retrieve_webfinger_is_called(self, mock_retrieve):
        retrieve_diaspora_hcard("bob@localhost")
        assert mock_retrieve.called_with("bob@localhost")

    @patch("federation.utils.diaspora.fetch_document")
    @patch("federation.utils.diaspora.retrieve_diaspora_webfinger")
    def test_fetch_document_is_called(self, mock_retrieve, mock_fetch):
        mock_retrieve.return_value = DiasporaWebFinger(
            "bob@localhost", "https://localhost", "123", "456"
        ).xrd
        mock_fetch.return_value = "document", None, None
        document = retrieve_diaspora_hcard("bob@localhost")
        mock_fetch.assert_called_with("https://localhost/hcard/users/123")
        assert document == "document"

    @patch("federation.utils.diaspora.fetch_document")
    @patch("federation.utils.diaspora.retrieve_diaspora_webfinger")
    def test_returns_none_on_fetch_document_exception(self, mock_retrieve, mock_fetch):
        mock_retrieve.return_value = DiasporaWebFinger(
            "bob@localhost", "https://localhost", "123", "456"
        ).xrd
        mock_fetch.return_value = None, None, ValueError()
        document = retrieve_diaspora_hcard("bob@localhost")
        mock_fetch.assert_called_with("https://localhost/hcard/users/123")
        assert document == None


class TestRetrieveDiasporaWebfinger(object):
    @patch("federation.utils.diaspora.retrieve_diaspora_host_meta", return_value=None)
    def test_retrieve_host_meta_is_called(self, mock_retrieve):
        retrieve_diaspora_webfinger("bob@localhost")
        mock_retrieve.assert_called_with("localhost")

    @patch("federation.utils.diaspora.XRD.parse_xrd")
    @patch("federation.utils.diaspora.fetch_document")
    @patch("federation.utils.diaspora.retrieve_diaspora_host_meta", return_value=None)
    def test_retrieve_fetch_document_is_called(self, mock_retrieve, mock_fetch, mock_xrd):
        mock_retrieve.return_value = DiasporaHostMeta(
            webfinger_host="https://localhost"
        ).xrd
        mock_fetch.return_value = "document", None, None
        mock_xrd.return_value = "document"
        document = retrieve_diaspora_webfinger("bob@localhost")
        mock_fetch.assert_called_with("https://localhost/webfinger?q=%s" % quote("bob@localhost"))
        assert document == "document"

    @patch("federation.utils.diaspora.fetch_document")
    @patch("federation.utils.diaspora.retrieve_diaspora_host_meta", return_value=None)
    def test_returns_none_on_fetch_document_exception(self, mock_retrieve, mock_fetch):
        mock_retrieve.return_value = DiasporaHostMeta(
            webfinger_host="https://localhost"
        ).xrd
        mock_fetch.return_value = None, None, ValueError()
        document = retrieve_diaspora_webfinger("bob@localhost")
        mock_fetch.assert_called_with("https://localhost/webfinger?q=%s" % quote("bob@localhost"))
        assert document == None


class TestRetrieveDiasporaHostMeta(object):
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
        assert document == None


class TestGetElementTextOrNone(object):
    doc = html.fromstring("<foo>bar</foo>")

    def test_text_returned_on_element(self):
        assert _get_element_text_or_none(self.doc, "foo") == "bar"

    def test_none_returned_on_no_element(self):
        assert _get_element_text_or_none(self.doc, "bar") == None


class TestGetElementAttrOrNone(object):
    doc = html.fromstring("<foo src='baz'>bar</foo>")

    def test_attr_returned_on_attr(self):
        assert _get_element_attr_or_none(self.doc, "foo", "src") == "baz"

    def test_none_returned_on_attr(self):
        assert _get_element_attr_or_none(self.doc, "foo", "href") == None

    def test_none_returned_on_no_element(self):
        assert _get_element_attr_or_none(self.doc, "bar", "href") == None


class TestParseProfileFromHCard(object):
    def test_profile_is_parsed(self):
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
        profile = parse_profile_from_hcard(hcard)
        assert profile.name == "fullname"
        assert profile.image_urls == {
            "small": "photo50", "medium": "photo100", "large": "photo300"
        }
        assert profile.public == True
        assert profile.handle == "username@hostname"
        assert profile.guid == "guid"
        assert profile.public_key == "public_key\n"


class TestRetrieveAndParseProfile(object):
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
        mock_parse.assert_called_with(hcard)
