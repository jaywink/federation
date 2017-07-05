import logging


# Should be implemented by submodules
PROTOCOL_NAME = None
PROTOCOL_NS = None
USER_AGENT = None


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

    def build_send(self, *args, **kwargs):
        """Build a payload for sending.

        Args:
            from_user (obj)         - The user object who is sending
                                      Must contain attributes `handle` and `private_key`
            to_user (obj)           - The user object we are sending to
                                      Must contain attribute `key` (public key)
            generator (function)    - Generator function to generate object for sending


        """
        raise NotImplementedError("Implement in subclass")

    def receive(self, payload, user=None, sender_key_fetcher=None):
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
