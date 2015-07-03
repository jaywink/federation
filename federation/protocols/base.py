import logging


# Should be implemented by submodules
PROTOCOL_NS = None
user_agent = None


def identify_payload(payload):
    """Each protocol module should define an `identify_payload` method.

    Args:
        payload (str)   - Payload blob

    Returns:
        True or False   - A boolean whether the payload matches this protocol.
    """
    raise NotImplementedError("Implement in protocol module")


class BaseProtocol(object):

    logger = logging.getLogger(__name__)

    def _build(self, *args, **kwargs):
        """Build a payload."""
        raise NotImplementedError("Implement in subclass")

    def send(self, *args, **kwargs):
        """Send a payload."""
        raise NotImplementedError("Implement in subclass")

    def receive(self, payload, user=None, sender_key_fetcher=None, *args, **kwargs):
        """Receive a payload.

        Args:
            payload (str)                           - Payload blob
            user (optional, obj)                    - Target user object
                                                      If given, MUST contain `key` attribute which corresponds to user
                                                      decrypted private key
            sender_key_fetcher (optional, func)     - Function that accepts sender handle and returns public key

        Returns tuple of:
            str - Sender handle ie user@domain.tld
            str - Extracted message body
        """
        raise NotImplementedError("Implement in subclass")
