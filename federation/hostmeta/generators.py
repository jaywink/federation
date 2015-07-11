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
