from enum import Enum
from typing import Optional, Dict, Union

import attr
# noinspection PyPackageRequirements
from Crypto.PublicKey import RSA
# noinspection PyPackageRequirements
from Crypto.PublicKey.RSA import RsaKey


@attr.s
class RequestType:
    """
    Emulates structure of a Django HttpRequest for compatibility.
    """
    body: Union[str, bytes] = attr.ib()

    # Required when dealing with incoming AP payloads
    headers: Dict = attr.ib(default=None)
    method: str = attr.ib(default=None)
    url: str = attr.ib(default=None)


class ReceiverVariant(Enum):
    # Indicates this receiver is a single actor
    ACTOR = "actor"
    # Indicates this receiver is the followers of this actor
    FOLLOWERS = "followers"


class UserVariant(Enum):
    """
    Indicates whether the user is local or remote.
    """
    LOCAL = "local"
    REMOTE = "remote"


@attr.s(frozen=True)
class UserType:
    id: str = attr.ib()
    private_key: Optional[Union[RsaKey, str]] = attr.ib(default=None)
    receiver_variant: Optional[ReceiverVariant] = attr.ib(default=None)

    # Required only if sending to Diaspora protocol platforms
    handle: Optional[str] = attr.ib(default=None)
    guid: Optional[str] = attr.ib(default=None)

    # Required only if sending to Matrix protocol
    username: Optional[str] = attr.ib(default=None)
    variant: Optional[UserVariant] = attr.ib(default=None)

    @property
    def rsa_private_key(self) -> RsaKey:
        if isinstance(self.private_key, str):
            return RSA.importKey(self.private_key)
        return self.private_key
