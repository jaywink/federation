class EncryptedMessageError(Exception):
    """Encrypted message could not be opened."""
    pass


class NoHeaderInMessageError(Exception):
    """Message payload is missing required header."""
    pass


class NoSenderKeyFoundError(Exception):
    """Sender private key was not available to sign a payload message."""
    pass


class NoSuitableProtocolFoundError(Exception):
    """No suitable protocol found to pass this payload message to."""
    pass
