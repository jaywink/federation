from typing import Optional, Dict, Union

import attr
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


@attr.s
class UserType:
    id: str = attr.ib()
    private_key: Optional[RsaKey] = attr.ib(default=None)

    # Required only if sending to Diaspora protocol platforms
    handle: Optional[str] = attr.ib(default=None)
    guid: Optional[str] = attr.ib(default=None)
