from typing import Optional

import attr


@attr.s
class UserType:
    id: str = attr.ib()
    private_key: Optional[str] = attr.ib(default=None)

    # Required only if sending to Diaspora protocol platforms
    handle: Optional[str] = attr.ib(default=None)
    guid: Optional[str] = attr.ib(default=None)
