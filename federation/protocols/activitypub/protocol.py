import json
import logging
import re
from typing import Callable, Tuple, Union, Dict

from cryptography.exceptions import InvalidSignature
from Crypto.PublicKey.RSA import RsaKey

from federation.entities.activitypub.enums import ActorType
from federation.entities.mixins import BaseEntity
from federation.entities.utils import get_profile
from federation.protocols.activitypub.signing import verify_request_signature
from federation.types import UserType, RequestType
from federation.utils.activitypub import retrieve_and_parse_document
from federation.utils.text import decode_if_bytes


logger = logging.getLogger('federation')

PROTOCOL_NAME = "activitypub"


def identify_id(id: str) -> bool:
    """
    Try to identify whether this is an ActivityPub ID.
    """
    return re.match(r'^https?://', id, flags=re.IGNORECASE) is not None


def identify_request(request: RequestType) -> bool:
    """
    Try to identify whether this is an ActivityPub request.
    """
    # noinspection PyBroadException
    try:
        data = json.loads(decode_if_bytes(request.body))
        if "@context" in data:
            return True
    except Exception:
        pass
    return False


class Protocol:
    actor = None
    get_contact_key = None
    payload = None
    request = None
    sender = None
    user = None

    def __init__(self, request=None, get_contact_key=None):
        # this is required for calls to verify on GET requests
        self.request = request
        self.get_contact_key = get_contact_key

    def build_send(self, entity: BaseEntity, from_user: UserType, to_user_key: RsaKey = None) -> Union[str, Dict]:
        """
        Build POST data for sending out to remotes.

        :param entity: The outbound ready entity for this protocol.
        :param from_user: The user sending this payload. Must have ``private_key`` and ``id`` properties.
        :param to_user_key: (Optional) Public key of user we're sending a private payload to.
        :returns: dict or string depending on if private or public payload.
        """
        if hasattr(entity, "outbound_doc") and entity.outbound_doc is not None:
            # Use pregenerated outbound document
            rendered = entity.outbound_doc
        else:
            rendered = entity.sign_as2(sender=from_user)
        return rendered

    def extract_actor(self):
        if self.payload.get('type') in ActorType.values():
            self.actor = self.payload.get('id')
        else:
            self.actor = self.payload.get('actor')

    def receive(
            self,
            request: RequestType,
            user: UserType = None,
            sender_key_fetcher: Callable[[str], str] = None,
            skip_author_verification: bool = False) -> Tuple[str, dict]:
        """
        Receive a request.

        For testing purposes, `skip_author_verification` can be passed. Authorship will not be verified.
        """
        self.user = user
        self.get_contact_key = sender_key_fetcher
        self.payload = json.loads(decode_if_bytes(request.body))
        self.request = request
        self.extract_actor()
        # Verify the message is from who it claims to be
        if not skip_author_verification:
            try:
                # Verify the HTTP signature
                self.verify()
            except (ValueError, KeyError, InvalidSignature) as exc:
                logger.warning('HTTP signature verification failed: %s', exc)
                return self.actor, {}
        return self.sender, self.payload

    def verify(self):
        sig_struct = self.request.headers.get("Signature", None)
        if not sig_struct:
            raise ValueError("A signature is required but was not provided")

        # this should return a dict populated with the following keys:
        # keyId, algorithm, headers and signature
        sig = {i.split("=", 1)[0]: i.split("=", 1)[1].strip('"') for i in sig_struct.split(",")}

        signer = get_profile(key_id=sig.get('keyId'))
        if not signer:
            signer = retrieve_and_parse_document(sig.get('keyId'))
        print(sig, signer)
        self.sender = signer.id if signer else self.actor
        key = getattr(signer, 'public_key', None)
        if not key:
            key = self.get_contact_key(self.actor) if self.get_contact_key and self.actor else ''
            if key:
                # fallback to the author's key the client app may have provided
                logger.warning("Failed to retrieve keyId for %s, trying the actor's key", sig.get('keyId'))
            else:
                raise ValueError(f"No public key for {sig.get('keyId')}")

        verify_request_signature(self.request, key=key, algorithm=sig.get('algorithm',""))
