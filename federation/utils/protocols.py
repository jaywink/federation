import re
from typing import Optional

from federation.utils.text import validate_handle


def identify_recipient_protocol(id: str) -> Optional[str]:
    if re.match(r'^https?://', id, flags=re.IGNORECASE) is not None:
        return "activitypub"
    if validate_handle(id):
        return "diaspora"
