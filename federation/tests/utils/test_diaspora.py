# -*- coding: utf-8 -*-
from unittest.mock import patch
from urllib.parse import quote

from federation.hostmeta.generators import DiasporaWebFinger, DiasporaHostMeta
from federation.utils.diaspora import retrieve_diaspora_hcard, retrieve_diaspora_webfinger, retrieve_diaspora_host_meta


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
