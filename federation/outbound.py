import json
import logging
from typing import List, Tuple, Union

from Crypto.PublicKey.RSA import RsaKey

from federation.entities.diaspora.mappers import get_outbound_entity
from federation.entities.mixins import BaseEntity
from federation.protocols.diaspora.protocol import Protocol
from federation.types import UserType
from federation.utils.diaspora import get_public_endpoint, get_private_endpoint
from federation.utils.network import send_document

logger = logging.getLogger("federation")


def handle_create_payload(
        entity:BaseEntity, author_user:UserType, to_user_key:RsaKey=None, parent_user:UserType=None) -> str:
    """Create a payload with the correct protocol.

    Any given user arguments must have ``private_key`` and ``handle`` attributes.

    :arg entity: Entity object to send. Can be a base entity or a protocol specific one.
    :arg author_user: User authoring the object.
    :arg to_user_key: Public key of user private payload is being sent to, required for private payloads.
    :arg parent_user: (Optional) User object of the parent object, if there is one. This must be given for the
                      Diaspora protocol if a parent object exists, so that a proper ``parent_author_signature`` can
                      be generated. If given, the payload will be sent as this user.
    :returns: Built payload message (str)
    """
    # Just use Diaspora protocol for now
    protocol = Protocol()
    outbound_entity = get_outbound_entity(entity, author_user.private_key)
    if parent_user:
        outbound_entity.sign_with_parent(parent_user.private_key)
    send_as_user = parent_user if parent_user else author_user
    data = protocol.build_send(entity=outbound_entity, from_user=send_as_user, to_user_key=to_user_key)
    return data


def handle_send(
        entity: BaseEntity,
        author_user: UserType,
        recipients: List[Union[Tuple[str, RsaKey], Tuple[str, RsaKey, str], str]]=None,
        parent_user: UserType=None,
) -> None:
    """Send an entity to remote servers.

    Using this we will build a list of payloads per protocol, after resolving any that need to be guessed or
    looked up over the network. After that, each recipient will get the generated protocol payload delivered.

    Any given user arguments must have ``private_key`` and ``id`` attributes.

    :arg entity: Entity object to send. Can be a base entity or a protocol specific one.
    :arg author_user: User authoring the object.
    :arg recipients: A list of recipients to delivery to. Each recipient is a tuple
                     containing at minimum the "id".
                     For private deliveries, optionally "public key" (all protocols) and "guid" (diaspora
                     protocol) are required.
                     Instead of a tuple, for public deliveries the "id" as str is also ok.
                     If public key and guid are provided, Diaspora protocol delivery will be made as an encrypted
                     private delivery.
                     For example
                     [
                         ("user@domain.tld", <RSAPublicKey object>, '1234-5678-0123-4567'),
                         ("user@domain2.tld", None, None),
                         "user@domain3.tld",
                         "https://domain4.tld/sharedinbox/",
                         ("https://domain4.tld/sharedinbox/", <RSAPublicKey object>),
                     ]
    :arg parent_user: (Optional) User object of the parent object, if there is one. This must be given for the
                      Diaspora protocol if a parent object exists, so that a proper ``parent_author_signature`` can
                      be generated. If given, the payload will be sent as this user.
    """
    payloads = []
    public_payloads = {
        "diaspora": {
            "payload": None,
            "urls": set(),
        },
    }

    # Generate payloads and collect urls
    for recipient in recipients:
        id = recipient[0] if isinstance(recipient, tuple) else recipient
        public_key = recipient[1] if isinstance(recipient, tuple) and len(recipient) > 1 else None
        if public_key:
            # Private payload
            try:
                payload = handle_create_payload(entity, author_user, to_user_key=public_key, parent_user=parent_user)
                payload = json.dumps(payload)
            except Exception as ex:
                logger.error("handle_send - failed to generate private payload for %s: %s", id, ex)
                continue
            # TODO get_private_endpoint should be imported per protocol
            guid = recipient[2] if len(recipient) > 2 else None
            url = get_private_endpoint(id, guid=guid)
            payloads.append({
                "urls": {url}, "payload": payload, "content_type": "application/json",
            })
        else:
            if not public_payloads["diaspora"]["payload"]:
                public_payloads["diaspora"]["payload"] = handle_create_payload(
                    entity, author_user, parent_user=parent_user,
                )
            # TODO get_public_endpoint should be imported per protocol
            url = get_public_endpoint(id)
            public_payloads["diaspora"]["urls"].add(url)

    # Add public payload
    if public_payloads["diaspora"]["payload"]:
        payloads.append({
            "urls": public_payloads["diaspora"]["urls"], "payload": public_payloads["diaspora"]["payload"],
            "content_type": "application/magic-envelope+xml",
        })

    logger.debug("handle_send - %s", payloads)

    # Do actual sending
    for payload in payloads:
        for url in payload["urls"]:
            try:
                send_document(url, payload["payload"], headers={"Content-Type": payload["content_type"]})
            except Exception as ex:
                logger.error("handle_send - failed to send payload to %s: %s, payload: %s", url, ex, payload["payload"])
