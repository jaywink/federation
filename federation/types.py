from typing import Optional

import attr


@attr.s
class UserType:
    id: str = attr.ib()
    private_key: Optional[str] = attr.ib(default=None)

    # Required only if sending to Diaspora protocol platforms
    handle: Optional[str] = attr.ib(default=None)
    guid: Optional[str] = attr.ib(default=None)

    @property
    def diaspora_id(self):
        from federation.utils.diaspora import generate_diaspora_profile_id  # Circulars

        if not self.handle:
            raise ValueError("Cannot generate UserType.diaspora_id without a handle")

        return generate_diaspora_profile_id(self.handle, guid=self.guid)
