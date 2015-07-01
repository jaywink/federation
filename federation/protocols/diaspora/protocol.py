from federation.protocols.base import BaseProtocol
from federation.protocols.diaspora.pyaspora import DiasporaMessageParser


class DiasporaProtocol(BaseProtocol):

    protocol_ns = "https://joindiaspora.com/protocol"
    user_agent = 'social-federation/diaspora/0.1'

    def __init__(self, *args, **kwargs):
        self._get_contact = kwargs.get("contact_fetcher")

    def _receive(self, payload, *args, **kwargs):
        """Receive a payload."""
        parser = DiasporaMessageParser(self._get_contact)
        ret, from_user = parser.decode(payload, None)
