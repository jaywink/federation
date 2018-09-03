import json
import os
import warnings
from base64 import b64encode
from string import Template

from jsonschema import validate
from jsonschema.exceptions import ValidationError
from xrd import XRD, Link, Element

from federation.utils.diaspora import parse_profile_diaspora_id


def generate_host_meta(template=None, *args, **kwargs):
    """Generate a host-meta XRD document.

    Template specific key-value pairs need to be passed as ``kwargs``, see classes.

    :arg template: Ready template to fill with args, for example "diaspora" (optional)
    :returns: Rendered XRD document (str)
    """
    if template == "diaspora":
        hostmeta = DiasporaHostMeta(*args, **kwargs)
    else:
        hostmeta = BaseHostMeta(*args, **kwargs)
    return hostmeta.render()


def generate_legacy_webfinger(template=None, *args, **kwargs):
    """Generate a legacy webfinger XRD document.

    Template specific key-value pairs need to be passed as ``kwargs``, see classes.

    :arg template: Ready template to fill with args, for example "diaspora" (optional)
    :returns: Rendered XRD document (str)
    """
    if template == "diaspora":
        webfinger = DiasporaWebFinger(*args, **kwargs)
    else:
        webfinger = BaseLegacyWebFinger(*args, **kwargs)
    return webfinger.render()


def generate_nodeinfo2_document(**kwargs):
    """
    Generate a NodeInfo2 document.

    Pass in a dictionary as per NodeInfo2 1.0 schema:
    https://github.com/jaywink/nodeinfo2/blob/master/schemas/1.0/schema.json

    Minimum required schema:
        {server:
          baseUrl
          name
          software
          version
        }
        openRegistrations

    Protocols default will match what this library supports, ie "diaspora" currently.

    :return: dict
    :raises: KeyError on missing required items
    """
    return {
        "version": "1.0",
        "server": {
            "baseUrl": kwargs['server']['baseUrl'],
            "name": kwargs['server']['name'],
            "software": kwargs['server']['software'],
            "version": kwargs['server']['version'],
        },
        "organization": {
            "name": kwargs.get('organization', {}).get('name', None),
            "contact": kwargs.get('organization', {}).get('contact', None),
            "account": kwargs.get('organization', {}).get('account', None),
        },
        "protocols": kwargs.get('protocols', ["diaspora"]),
        "relay": kwargs.get('relay', ''),
        "services": {
            "inbound": kwargs.get('service', {}).get('inbound', []),
            "outbound": kwargs.get('service', {}).get('outbound', []),
        },
        "openRegistrations": kwargs['openRegistrations'],
        "usage": {
            "users": {
                "total": kwargs.get('usage', {}).get('users', {}).get('total'),
                "activeHalfyear": kwargs.get('usage', {}).get('users', {}).get('activeHalfyear'),
                "activeMonth": kwargs.get('usage', {}).get('users', {}).get('activeMonth'),
                "activeWeek": kwargs.get('usage', {}).get('users', {}).get('activeWeek'),
            },
            "localPosts": kwargs.get('usage', {}).get('localPosts'),
            "localComments": kwargs.get('usage', {}).get('localComments'),
        }
    }


def generate_hcard(template=None, **kwargs):
    """Generate a hCard document.

    Template specific key-value pairs need to be passed as ``kwargs``, see classes.

    :arg template: Ready template to fill with args, for example "diaspora" (optional)
    :returns: HTML document (str)
    """
    if template == "diaspora":
        hcard = DiasporaHCard(**kwargs)
    else:
        raise NotImplementedError()
    return hcard.render()


class BaseHostMeta:
    def __init__(self, *args, **kwargs):
        self.xrd = XRD()

    def render(self):
        return self.xrd.to_xml().toprettyxml(indent="  ", encoding="UTF-8")


class DiasporaHostMeta(BaseHostMeta):
    """Diaspora host-meta.

    Required keyword args:

    * webfinger_host (str)
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        link = Link(
            rel='lrdd',
            type_='application/xrd+xml',
            template='%s/webfinger?q={uri}' % kwargs["webfinger_host"]
        )
        self.xrd.links.append(link)


class BaseLegacyWebFinger(BaseHostMeta):
    """Legacy XRD WebFinger.

    See: https://code.google.com/p/webfinger/wiki/WebFingerProtocol
    """
    def __init__(self, address, *args, **kwargs):
        super().__init__(*args, **kwargs)
        subject = Element("Subject", "acct:%s" % address)
        self.xrd.elements.append(subject)


class DiasporaWebFinger(BaseLegacyWebFinger):
    """Diaspora version of legacy WebFinger.

    Required keyword args:

    * handle (str)        - eg user@domain.tld
    * host (str)          - eg https://domain.tld
    * guid (str)          - guid of user
    * public_key (str)    - public key
    """
    def __init__(self, handle, host, guid, public_key, *args, **kwargs):
        super().__init__(handle, *args, **kwargs)
        self.xrd.elements.append(Element("Alias", "%s/people/%s" % (
            host, guid
        )))
        username = handle.split("@")[0]
        self.xrd.links.append(Link(
            rel="http://microformats.org/profile/hcard",
            type_="text/html",
            href="%s/hcard/users/%s" %(
                host, guid
            )
        ))
        self.xrd.links.append(Link(
            rel="http://joindiaspora.com/seed_location",
            type_="text/html",
            href=host
        ))
        self.xrd.links.append(Link(
            rel="http://joindiaspora.com/guid",
            type_="text/html",
            href=guid
        ))
        self.xrd.links.append(Link(
            rel="http://webfinger.net/rel/profile-page",
            type_="text/html",
            href="%s/u/%s" % (
                host, username
            )
        ))
        self.xrd.links.append(Link(
            rel="http://schemas.google.com/g/2010#updates-from",
            type_="application/atom+xml",
            href="%s/public/%s.atom" % (
                host, username
            )
        ))
        # Base64 the key
        # See https://wiki.diasporafoundation.org/Federation_Protocol_Overview#Diaspora_Public_Key
        try:
            base64_key = b64encode(bytes(public_key, encoding="UTF-8")).decode("ascii")
        except TypeError:
            # Python 2
            base64_key = b64encode(public_key).decode("ascii")
        self.xrd.links.append(Link(
            rel="diaspora-public-key",
            type_="RSA",
            href=base64_key
        ))


class DiasporaHCard:
    """Diaspora hCard document.

    Must receive the `required` attributes as keyword arguments to init.
    """

    required = [
        "hostname", "fullname", "firstname", "lastname", "photo300", "photo100", "photo50", "searchable", "guid", "public_key", "username",
    ]

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        template_path = os.path.join(os.path.dirname(__file__), "templates", "hcard_diaspora.html")
        with open(template_path) as f:
            self.template = Template(f.read())

    def render(self):
        required = self.required[:]
        for key, value in self.kwargs.items():
            required.remove(key)
            assert value is not None
            assert isinstance(value, str)
        assert len(required) == 0
        return self.template.substitute(self.kwargs)


class SocialRelayWellKnown:
    """A `.well-known/social-relay` document in JSON.

    For apps wanting to announce their preferences towards relay applications.

    See WIP spec: https://wiki.diasporafoundation.org/Relay_servers_for_public_posts

    Schema see `schemas/social-relay-well-known.json`

    :arg subscribe: bool
    :arg tags: tuple, optional
    :arg scope: Should be either "all" or "tags", default is "all" if not given
    """
    def __init__(self, subscribe, tags=(), scope="all", *args, **kwargs):
        self.doc = {
            "subscribe": subscribe,
            "scope": scope,
            "tags": list(tags),
        }

    def render(self):
        self.validate_doc()
        return json.dumps(self.doc)

    def validate_doc(self):
        schema_path = os.path.join(os.path.dirname(__file__), "schemas", "social-relay-well-known.json")
        with open(schema_path) as f:
            schema = json.load(f)
        validate(self.doc, schema)


class NodeInfo:
    """Generate a NodeInfo document.

    See spec: http://nodeinfo.diaspora.software

    NodeInfo is unnecessarely restrictive in field values. We wont be supporting such strictness, though
    we will raise a warning unless validation is skipped with `skip_validate=True`.

    For strictness, `raise_on_validate=True` will cause a `ValidationError` to be raised.

    See schema document `federation/hostmeta/schemas/nodeinfo-1.0.json` for how to instantiate this class.
    """

    def __init__(self, software, protocols, services, open_registrations, usage, metadata, skip_validate=False,
                 raise_on_validate=False):
        self.doc = {
            "version": "1.0",
            "software": software,
            "protocols": protocols,
            "services": services,
            "openRegistrations": open_registrations,
            "usage": usage,
            "metadata": metadata,
        }
        self.skip_validate = skip_validate
        self.raise_on_validate = raise_on_validate

    def render(self):
        if not self.skip_validate:
            self.validate_doc()
        return json.dumps(self.doc)

    def validate_doc(self):
        schema_path = os.path.join(os.path.dirname(__file__), "schemas", "nodeinfo-1.0.json")
        with open(schema_path) as f:
            schema = json.load(f)
        try:
            validate(self.doc, schema)
        except ValidationError:
            if self.raise_on_validate:
                raise
            warnings.warn("NodeInfo document generated does not validate against NodeInfo 1.0 specification.")


# The default NodeInfo document path
NODEINFO_DOCUMENT_PATH = "/nodeinfo/1.0"


def get_nodeinfo_well_known_document(url, document_path=None):
    """Generate a NodeInfo .well-known document.

    See spec: http://nodeinfo.diaspora.software

    :arg url: The full base url with protocol, ie https://example.com
    :arg document_path: Custom NodeInfo document path if supplied (optional)
    :returns: dict
    """
    return {
        "links": [
            {
                "rel": "http://nodeinfo.diaspora.software/ns/schema/1.0",
                "href": "{url}{path}".format(
                    url=url, path=document_path or NODEINFO_DOCUMENT_PATH
                )
            }
        ]
    }


class RFC3033Webfinger:
    """
    RFC 3033 webfinger - see https://diaspora.github.io/diaspora_federation/discovery/webfinger.html

    A Django view is also available, see the child ``django`` module for view and url configuration.

    :param id: Diaspora ID in URI format
    :param base_url: The base URL of the server (protocol://domain.tld)
    :param profile_path: Profile path for the user (for example `/profile/johndoe/`)
    :param hcard_path: (Optional) hCard path, defaults to ``/hcard/users/``.
    :param atom_path: (Optional) atom feed path
    :returns: dict
    """
    def __init__(
            self, handle, guid, base_url, profile_path, hcard_path="/hcard/users/", atom_path=None, search_path=None,
    ):
        self.handle = handle
        self.guid = guid
        self.base_url = base_url
        self.hcard_path = hcard_path
        self.profile_path = profile_path
        self.atom_path = atom_path
        self.search_path = search_path

    def render(self):
        webfinger = {
            "subject": "acct:%s" % self.handle,
            "links": [
                {
                    "rel": "http://microformats.org/profile/hcard",
                    "type": "text/html",
                    "href": "%s%s%s" % (self.base_url, self.hcard_path, self.guid),
                },
                {
                    "rel": "http://joindiaspora.com/seed_location",
                    "type": "text/html",
                    "href": self.base_url,
                },
                {
                    "rel": "http://webfinger.net/rel/profile-page",
                    "type": "text/html",
                    "href": "%s%s" % (self.base_url, self.profile_path),
                },
                {
                    "rel": "salmon",
                    "href": "%s/receive/users/%s" % (self.base_url, self.guid),
                },
            ],
        }
        if self.atom_path:
            webfinger['links'].append(
                {
                    "rel": "http://schemas.google.com/g/2010#updates-from",
                    "type": "application/atom+xml",
                    "href": "%s%s" % (self.base_url, self.atom_path),
                }
            )
        if self.search_path:
            webfinger['links'].append(
                {
                    "rel": "http://ostatus.org/schema/1.0/subscribe",
                    "template": "%s%s{uri}" % (self.base_url, self.search_path),
                },
            )
        return webfinger
