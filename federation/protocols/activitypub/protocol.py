import json
from typing import Union

from federation.utils.text import decode_if_bytes


def identify_payload(payload: Union[str, bytes]) -> bool:
    """
    Try to identify whether this is an ActivityPub payload.
    """
    try:
        data = json.loads(decode_if_bytes(payload))
        if "@context" in data:
            return True
    except Exception:
        pass
    return False
