import json
import logging
import re
from typing import Callable, Tuple, List, Dict

from federation.entities.matrix.entities import MatrixEntityMixin
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

    # noinspection PyUnusedLocal
    @staticmethod
    def build_send(entity: MatrixEntityMixin, *args, **kwargs) -> List[Dict]:
        """
        Build POST data for sending out to the homeserver.

        :param entity: The outbound ready entity for this protocol.
        :returns: list of payloads
        """
        return entity.payloads()

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
