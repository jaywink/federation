from xrd import XRD, Link


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


class BaseHostMeta(object):
    def __init__(self, *args, **kwargs):
        self.xrd = XRD()

    def render(self):
        return self.xrd.to_xml()


class DiasporaHostMeta(BaseHostMeta):
    """Diaspora host-meta.

    NOTE! Diaspora .well-known/host-meta seems to define 'encoding="UTF-8"' from server implementation.
    The xrd.XRD module does not define this or allow defining it when rendering the XML. This will need to be
    fixed if that is a problem to Diaspora or other servers.

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
