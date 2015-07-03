import logging


def identify_payload(payload):
    """Each protocol module should define an 'identify_payload' method.

    Args:
        payload (str) - Payload blob

    Returns:
        True or False - A boolean whether the payload matches this protocol.
    """
    raise NotImplementedError("Implement in protocol module")


class BaseProtocol(object):

    # Should be implemented by subclasses
    protocol_ns = None
    user_agent = None

    logger = logging.getLogger(__name__)

    def _build(self, *args, **kwargs):
        """Build a payload."""
        raise NotImplementedError("Implement in subclass")

    def send(self, *args, **kwargs):
        """Send a payload."""
        raise NotImplementedError("Implement in subclass")

    def receive(self, payload, user=None, *args, **kwargs):
        """Receive a payload.

        Args:
            payload (str) - Payload blob
            user (object) - Optional target user entry
                            If given, MUST contain `key` attribute which corresponds to user
                            decrypted private key

        Returns tuple of:
            str - Sender handle ie user@domain.tld
            str - Extracted message body
        """
        raise NotImplementedError("Implement in subclass")
