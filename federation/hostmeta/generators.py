from base64 import b64encode
import os
from string import Template
from xrd import XRD, Link, Element


def generate_host_meta(template=None, *args, **kwargs):
    """Generate a host-meta XRD document.

    Args:
        template (str, optional)    - Ready template to fill with args, for example "diaspora".
        **kwargs                    - Template specific key-value pairs to fill in, see classes.

    Returns:
        str                         - XRD document
    """
    if template == "diaspora":
        hostmeta = DiasporaHostMeta(*args, **kwargs)
    else:
        hostmeta = BaseHostMeta(*args, **kwargs)
    return hostmeta.render()


def generate_legacy_webfinger(template=None, *args, **kwargs):
    """Generate a legacy webfinger XRD document.

    Args:
        template (str, optional)    - Ready template to fill with args, for example "diaspora".
        **kwargs                    - Template specific key-value pairs to fill in, see classes.

    Returns:
        str                         - XRD document
    """
    if template == "diaspora":
        webfinger = DiasporaWebFinger(*args, **kwargs)
    else:
        webfinger = BaseLegacyWebFinger(*args, **kwargs)
    return webfinger.render()


def generate_hcard(template=None, **kwargs):
    """Generate a hCard document.

    Args:
        template (str, optional)    - Ready template to fill with args, for example "diaspora".
        **kwargs                    - Template specific key-value pairs to fill in, see classes.

    Returns:
        str                         - HTML document
    """
    if template == "diaspora":
        hcard = DiasporaHCard(**kwargs)
    else:
        raise NotImplementedError()
    return hcard.render()


class BaseHostMeta(object):
    def __init__(self, *args, **kwargs):
        self.xrd = XRD()

    def render(self):
        return self.xrd.to_xml().toprettyxml(indent="  ", encoding="UTF-8")


class DiasporaHostMeta(BaseHostMeta):
    """Diaspora host-meta.

    Requires keyword args:
        webfinger_host (str)
    """
    def __init__(self, *args, **kwargs):
        super(DiasporaHostMeta, self).__init__(*args, **kwargs)
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
        super(BaseLegacyWebFinger, self).__init__(*args, **kwargs)
        subject = Element("Subject", "acct:%s" % address)
        self.xrd.elements.append(subject)


class DiasporaWebFinger(BaseLegacyWebFinger):
    """Diaspora version of legacy WebFinger.

    Requires keyword args:
        handle (str)        - eg user@domain.tld
        host (str)          - eg https://domain.tld
        guid (str)          - guid of user
        public_key (str)    - public key
    """
    def __init__(self, handle, host, guid, public_key, *args, **kwargs):
        super(DiasporaWebFinger, self).__init__(handle, *args, **kwargs)
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
        base64_key = b64encode(bytes(public_key, encoding="UTF-8")).decode("ascii")
        self.xrd.links.append(Link(
            rel="diaspora-public-key",
            type_="RSA",
            href=base64_key
        ))


class DiasporaHCard(object):
    """Diaspora hCard document.

    Must receive the `required` attributes as keyword arguments to init.
    """

    required = [
        "hostname", "fullname", "firstname", "lastname", "photo300", "photo100", "photo50", "searchable",
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
