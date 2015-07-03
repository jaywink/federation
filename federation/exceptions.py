class EncryptedMessageError(Exception):
    pass


class NoHeaderInMessageError(Exception):
    pass


class NoSenderKeyFoundError(Exception):
    pass


class NoSuitableProtocolFoundError(Exception):
    pass
