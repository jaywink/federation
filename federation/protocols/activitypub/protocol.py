import json
from typing import Union, Callable, Tuple

from federation.types import UserType
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


class Protocol:
    def receive(self, payload: str, user: UserType=None, sender_key_fetcher: Callable[[str], str]=None,
            skip_author_verification: bool=False) -> Tuple[str, str]:
        """
        Receive a payload.

        For testing purposes, `skip_author_verification` can be passed. Authorship will not be verified.
        """
        self.user = user
        self.get_contact_key = sender_key_fetcher
        self.payload = json.loads(decode_if_bytes(payload))
        # Verify the message is from who it claims to be
        if not skip_author_verification:
            self.verify_signature()
        return self.payload["actor"], self.payload

    def verify_signature(self):
        # TODO implement
        pass
