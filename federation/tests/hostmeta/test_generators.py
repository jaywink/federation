# -*- coding: utf-8 -*-
import json
from jsonschema import validate, ValidationError
import pytest

from federation.hostmeta.generators import generate_host_meta, generate_legacy_webfinger, generate_hcard, \
    SocialRelayWellKnown, NodeInfo, get_nodeinfo_well_known_document
from federation.tests.fixtures.payloads import DIASPORA_HOSTMETA, DIASPORA_WEBFINGER


class TestDiasporaHostMetaGenerator(object):

    def test_generate_valid_host_meta(self):
        hostmeta = generate_host_meta("diaspora", webfinger_host="https://example.com")
        assert hostmeta.decode("UTF-8") == DIASPORA_HOSTMETA

    def test_generate_host_meta_requires_webfinger_host(self):
        with pytest.raises(KeyError):
            generate_host_meta("diaspora")


class TestDiasporaWebFingerGenerator(object):

    def test_generate_valid_webfinger(self):
        webfinger = generate_legacy_webfinger(
            "diaspora",
            handle="user@server.example",
            host="https://server.example",
            guid="0123456789abcdef",
            public_key="ABCDEF=="
        )
        assert webfinger.decode("UTF-8") == DIASPORA_WEBFINGER

    def test_diaspora_webfinger_raises_on_missing_arguments(self):
        with pytest.raises(TypeError):
            generate_legacy_webfinger("diaspora")


class TestDiasporaHCardGenerator(object):

    def test_generate_valid_hcard(self):
        with open("federation/hostmeta/templates/hcard_diaspora.html") as f:
            template = f.read().replace("$", "")
        hcard = generate_hcard(
            "diaspora",
            hostname="hostname",
            fullname="fullname",
            firstname="firstname",
            lastname="lastname",
            photo300="photo300",
            photo100="photo100",
            photo50="photo50",
            searchable="searchable",
            guid="guid",
            public_key="public_key",
            username="username",
        )
        assert hcard == template

    def test_generate_hcard_raises_on_missing_attribute(self):
        with pytest.raises(AssertionError):
            generate_hcard(
                "diaspora",
                hostname="hostname",
                fullname="fullname",
                firstname="firstname"
            )

    def test_generate_hcard_raises_on_unknown_attribute(self):
        with pytest.raises(ValueError):
            generate_hcard(
                "diaspora",
                hostname="hostname",
                fullname="fullname",
                firstname="firstname",
                unknown="unknown"
            )


class TestSocialRelayWellKnownGenerator(object):

    def test_valid_social_relay_well_known(self):
        with open("federation/hostmeta/schemas/social-relay-well-known.json") as f:
            schema = json.load(f)
        well_known = SocialRelayWellKnown(subscribe=True, tags=("foo", "bar"), scope="tags")
        assert well_known.doc["subscribe"] == True
        assert well_known.doc["tags"] == ["foo", "bar"]
        assert well_known.doc["scope"] == "tags"
        validate(well_known.doc, schema)

    def test_valid_social_relay_well_known_empty_tags(self):
        with open("federation/hostmeta/schemas/social-relay-well-known.json") as f:
            schema = json.load(f)
        well_known = SocialRelayWellKnown(subscribe=False)
        assert well_known.doc["subscribe"] == False
        assert well_known.doc["tags"] == []
        assert well_known.doc["scope"] == "all"
        validate(well_known.doc, schema)

    def test_invalid_social_relay_well_known(self):
        with open("federation/hostmeta/schemas/social-relay-well-known.json") as f:
            schema = json.load(f)
        well_known_doc = {
            "subscribe": "true",
            "tags": "foo,bar",
            "someotherstuff": True,
        }
        with pytest.raises(ValidationError):
            validate(well_known_doc, schema)

    def test_invalid_social_relay_well_known_scope(self):
        with open("federation/hostmeta/schemas/social-relay-well-known.json") as f:
            schema = json.load(f)
        well_known = SocialRelayWellKnown(subscribe=True, tags=("foo", "bar"), scope="cities")
        with pytest.raises(ValidationError):
            validate(well_known.doc, schema)

    def test_render_validates_valid_document(self):
        well_known = SocialRelayWellKnown(subscribe=True, tags=("foo", "bar"), scope="tags")
        well_known.render()

    def test_render_validates_invalid_document(self):
        well_known = SocialRelayWellKnown(subscribe=True, tags=("foo", "bar"), scope="cities")
        with pytest.raises(ValidationError):
            well_known.render()


class TestNodeInfoGenerator(object):
    def _valid_nodeinfo(self, raise_on_validate=False):
        return NodeInfo(
            software={"name": "diaspora", "version": "0.5.4.3"},
            protocols={"inbound": ["diaspora"], "outbound": ["diaspora"]},
            services={"inbound": ["pumpio"], "outbound": ["twitter"]},
            open_registrations=True,
            usage={"users": {}},
            metadata={},
            raise_on_validate=raise_on_validate
        )

    def _invalid_nodeinfo(self, raise_on_validate=False):
        return NodeInfo(
            software={"name": "diaspora", "version": "0.5.4.3", "what_is_this_evil_key_here": True},
            protocols={"inbound": ["diaspora"], "outbound": ["diaspora"]},
            services={"inbound": ["pumpio"], "outbound": ["twitter"]},
            open_registrations=True,
            usage={"users": {}},
            metadata={},
            raise_on_validate=raise_on_validate
        )

    def test_nodeinfo_generator(self):
        nodeinfo = self._valid_nodeinfo()
        assert nodeinfo.doc["version"] == "1.0"
        assert nodeinfo.doc["software"] == {"name": "diaspora", "version": "0.5.4.3"}
        assert nodeinfo.doc["protocols"] == {"inbound": ["diaspora"], "outbound": ["diaspora"]}
        assert nodeinfo.doc["services"] == {"inbound": ["pumpio"], "outbound": ["twitter"]}
        assert nodeinfo.doc["openRegistrations"] == True
        assert nodeinfo.doc["usage"] == {"users": {}}
        assert nodeinfo.doc["metadata"] == {}

    def test_nodeinfo_generator_raises_on_invalid_nodeinfo_and_raise_on_validate(self):
        nodeinfo = self._invalid_nodeinfo(raise_on_validate=True)
        with pytest.raises(ValidationError):
            nodeinfo.render()

    def test_nodeinfo_generator_does_not_raise_on_invalid_nodeinfo(self):
        nodeinfo = self._invalid_nodeinfo()
        nodeinfo.render()

    def test_nodeinfo_generator_does_not_raise_on_valid_nodeinfo_and_raise_on_validate(self):
        nodeinfo = self._valid_nodeinfo(raise_on_validate=True)
        nodeinfo.render()

    def test_nodeinfo_generator_render_returns_a_document(self):
        nodeinfo = self._valid_nodeinfo()
        assert isinstance(nodeinfo.render(), str)

    def test_nodeinfo_wellknown_document(self):
        wellknown = get_nodeinfo_well_known_document("https://example.com")
        assert wellknown["links"][0]["rel"] == "http://nodeinfo.diaspora.software/ns/schema/1.0"
        assert wellknown["links"][0]["href"] == "https://example.com/nodeinfo/1.0"
