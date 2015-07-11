import pytest
from federation.hostmeta.generators import generate_host_meta


DIASPORA_HOSTMETA = """<?xml version="1.0" encoding="UTF-8"?>
<XRD xmlns="http://docs.oasis-open.org/ns/xri/xrd-1.0">
  <Link rel="lrdd" template="https://example.com/webfinger?q={uri}" type="application/xrd+xml"/>
</XRD>
"""


class TestDiasporaHostMetaGenerator(object):

    def test_generate_valid_host_meta(self):
        hostmeta = generate_host_meta("diaspora", webfinger_host="https://example.com")
        assert hostmeta.decode("UTF-8") == DIASPORA_HOSTMETA

    def test_generate_host_meta_requires_webfinger_host(self):
        with pytest.raises(KeyError):
            generate_host_meta("diaspora")
