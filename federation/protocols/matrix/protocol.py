import json
import logging
import re
from typing import Callable, Tuple, Union, Dict

# noinspection PyPackageRequirements
from Crypto.PublicKey.RSA import RsaKey

from federation.entities.mixins import BaseEntity
from federation.types import UserType, RequestType
from federation.utils.text import decode_if_bytes

logger = logging.getLogger('federation')

PROTOCOL_NAME = "activitypub"


def identify_id(identifier: str) -> bool:
    """
    Try to identify whether this is a Matrix identifier.

    TODO fix, not entirely correct..
    """
    return re.match(r'^[@#!].*:.*$', identifier, flags=re.IGNORECASE) is not None


def identify_request(request: RequestType) -> bool:
    """
    Try to identify whether this is a Matrix request
    """
    # noinspection PyBroadException
    try:
        data = json.loads(decode_if_bytes(request.body))
        if "events" in data:
            return True
    except Exception:
        pass
    return False


class Protocol:
    actor = None
    get_contact_key = None
    payload = None
    request = None
    user = None

    def build_send(self, entity: BaseEntity, from_user: UserType, to_user_key: RsaKey = None) -> Union[str, Dict]:
        """
        Build POST data for sending out to the homeserver.

        :param entity: The outbound ready entity for this protocol.
        :param from_user: The user sending this payload. Must have ``private_key`` and ``id`` properties.
        :param to_user_key: (Optional) Public key of user we're sending a private payload to.
        :returns: dict or string depending on if private or public payload.
        """
        # TODO TBD
        return {}

    def extract_actor(self):
        # TODO TBD
        pass

    def receive(
            self,
            request: RequestType,
            user: UserType = None,
            sender_key_fetcher: Callable[[str], str] = None,
            skip_author_verification: bool = False) -> Tuple[str, dict]:
        """
        Receive a request.

        Matrix appservices will deliver 1+ events at a time.
        """
        # TODO TBD
        return self.actor, self.payload
