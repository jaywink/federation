import json
from jsonschema import validate, ValidationError
import pytest

from federation.hostmeta.generators import generate_host_meta, generate_legacy_webfinger, generate_hcard, \
    SocialRelayWellKnown

DIASPORA_HOSTMETA = """<?xml version="1.0" encoding="UTF-8"?>
<XRD xmlns="http://docs.oasis-open.org/ns/xri/xrd-1.0">
  <Link rel="lrdd" template="https://example.com/webfinger?q={uri}" type="application/xrd+xml"/>
</XRD>
"""

DIASPORA_WEBFINGER = """<?xml version="1.0" encoding="UTF-8"?>
<XRD xmlns="http://docs.oasis-open.org/ns/xri/xrd-1.0">
  <Subject>acct:user@server.example</Subject>
  <Alias>https://server.example/people/0123456789abcdef</Alias>
  <Link href="https://server.example/hcard/users/0123456789abcdef" rel="http://microformats.org/profile/hcard" type="text/html"/>
  <Link href="https://server.example" rel="http://joindiaspora.com/seed_location" type="text/html"/>
  <Link href="0123456789abcdef" rel="http://joindiaspora.com/guid" type="text/html"/>
  <Link href="https://server.example/u/user" rel="http://webfinger.net/rel/profile-page" type="text/html"/>
  <Link href="https://server.example/public/user.atom" rel="http://schemas.google.com/g/2010#updates-from" type="application/atom+xml"/>
  <Link href="QUJDREVGPT0=" rel="diaspora-public-key" type="RSA"/>
</XRD>
"""


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
            searchable="searchable"
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
                username="username"
            )


class TestSocialRelayWellKnownGenerator(object):

    def test_valid_social_relay_well_known(self):
        with open("federation/tests/schemas/social-relay-well-known") as f:
            schema = json.load(f)
        well_known = SocialRelayWellKnown(subscribe=True, tags=("foo", "bar"))
        assert well_known.doc["subscribe"] == True
        assert well_known.doc["tags"] == ["foo", "bar"]
        validate(well_known.doc, schema)

    def test_valid_social_relay_well_known_empty_tags(self):
        with open("federation/tests/schemas/social-relay-well-known") as f:
            schema = json.load(f)
        well_known = SocialRelayWellKnown(subscribe=False)
        assert well_known.doc["subscribe"] == False
        assert well_known.doc["tags"] == []
        validate(well_known.doc, schema)

    def test_invalid_social_relay_well_known(self):
        with open("federation/tests/schemas/social-relay-well-known") as f:
            schema = json.load(f)
        well_known_doc = {
            "subscribe": "true",
            "tags": "foo,bar",
            "someotherstuff": True,
        }
        with pytest.raises(ValidationError):
            validate(well_known_doc, schema)
