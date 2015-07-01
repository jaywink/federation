import logging


class BaseProtocol(object):

    # Must be implemented by subclasses
    protocol_ns = None
    user_agent = None

    logger = logging.getLogger(__name__)

    def _build(self, *args, **kwargs):
        """Build a payload."""
        raise NotImplementedError("Implement in subclass")

    def _send(self, *args, **kwargs):
        """Send a payload."""
        raise NotImplementedError("Implement in subclass")

    def _receive(self, *args, **kwargs):
        """Receive a payload."""
        raise NotImplementedError("Implement in subclass")

    def _get_contact(self, handle, *args, **kwargs):
        """Some protocols require retrieving locally stored remote contact."""
        raise NotImplementedError("Implement in subclass")
