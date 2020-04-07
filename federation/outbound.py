import copy
import importlib
import json
import logging
import traceback
from typing import List, Dict, Union

# noinspection PyPackageRequirements
from Crypto.PublicKey import RSA
from Crypto.PublicKey.RSA import RsaKey
from iteration_utilities import unique_everseen

from federation.entities.activitypub.constants import NAMESPACE_PUBLIC
from federation.entities.mixins import BaseEntity
from federation.protocols.activitypub.signing import get_http_authentication
from federation.types import UserType
from federation.utils.network import send_document

logger = logging.getLogger("federation")


def handle_create_payload(
        entity: BaseEntity,
        author_user: UserType,
        protocol_name: str,
        to_user_key: RsaKey = None,
        parent_user: UserType = None,
        payload_logger: callable = None,
) -> Union[str, dict]:
    """Create a payload with the given protocol.

    Any given user arguments must have ``private_key`` and ``handle`` attributes.

    :arg entity: Entity object to send. Can be a base entity or a protocol specific one.
    :arg author_user: User authoring the object.
    :arg protocol_name: Protocol to create payload for.
    :arg to_user_key: Public key of user private payload is being sent to, required for private payloads.
    :arg parent_user: (Optional) User object of the parent object, if there is one. This must be given for the
                      Diaspora protocol if a parent object exists, so that a proper ``parent_author_signature`` can
                      be generated. If given, the payload will be sent as this user.
    :arg payload_logger: (Optional) Function to log the payloads with.

    :returns: Built payload (str or dict)
    """
    mappers = importlib.import_module(f"federation.entities.{protocol_name}.mappers")
    protocol = importlib.import_module(f"federation.protocols.{protocol_name}.protocol")
    protocol = protocol.Protocol()
    outbound_entity = mappers.get_outbound_entity(entity, author_user.rsa_private_key)
    if parent_user:
        outbound_entity.sign_with_parent(parent_user.rsa_private_key)
    send_as_user = parent_user if parent_user else author_user
    data = protocol.build_send(entity=outbound_entity, from_user=send_as_user, to_user_key=to_user_key)
    if payload_logger:
        try:
            payload_logger(data, protocol_name, author_user.id)
        except Exception as ex:
            logger.warning("handle_create_payload | Failed to log payload: %s" % ex)
    return data


def handle_send(
        entity: BaseEntity,
        author_user: UserType,
        recipients: List[Dict],
        parent_user: UserType = None,
        payload_logger: callable = None,
) -> None:
    """Send an entity to remote servers.

    Using this we will build a list of payloads per protocol. After that, each recipient will get the generated
    protocol payload delivered. Delivery to the same endpoint will only be done once so it's ok to include
    the same endpoint as a receiver multiple times.

    Any given user arguments must have ``private_key`` and ``fid`` attributes.

    :arg entity: Entity object to send. Can be a base entity or a protocol specific one.
    :arg author_user: User authoring the object.
    :arg recipients: A list of recipients to delivery to. Each recipient is a dict
                     containing at minimum the "endpoint", "fid", "public" and "protocol" keys.

                     For ActivityPub and Diaspora payloads, "endpoint" should be an URL of the endpoint to deliver to.

                     The "fid" can be empty for Diaspora payloads. For ActivityPub it should be the recipient
                     federation ID should the delivery be non-private.

                     The "protocol" should be a protocol name that is known for this recipient.

                     The "public" value should be a boolean to indicate whether the payload should be flagged as a
                     public payload.

                     TODO: support guessing the protocol over networks? Would need caching of results

                     For private deliveries to Diaspora protocol recipients, "public_key" is also required.

                     For example
                     [
                        {
                            "endpoint": "https://domain.tld/receive/users/1234-5678-0123-4567",
                            "fid": "",
                            "protocol": "diaspora",
                            "public": False,
                            "public_key": <RSAPublicKey object> | str,
                        },
                        {
                            "endpoint": "https://domain2.tld/receive/public",
                            "fid": "",
                            "protocol": "diaspora",
                            "public": True,
                        },
                        {
                            "endpoint": "https://domain4.tld/sharedinbox/",
                            "fid": "https://domain4.tld/profiles/jack/",
                            "protocol": "activitypub",
                            "public": True,
                        },
                        {
                            "endpoint": "https://domain4.tld/profiles/jill/inbox",
                            "fid": "https://domain4.tld/profiles/jill",
                            "protocol": "activitypub",
                            "public": False,
                        },
                     ]
    :arg parent_user: (Optional) User object of the parent object, if there is one. This must be given for the
                      Diaspora protocol if a parent object exists, so that a proper ``parent_author_signature`` can
                      be generated. If given, the payload will be sent as this user.
    :arg payload_logger: (Optional) Function to log the payloads with.
    """
    payloads = []
    ready_payloads = {
        "activitypub": {
            "auth": None,
            "payload": None,
            "urls": set(),
        },
        "diaspora": {
            "auth": None,
            "payload": None,
            "urls": set(),
        },
    }
    skip_ready_payload = {
        "activitypub": False,
        "diaspora": False,
    }

    # Flatten to unique recipients
    # TODO supply a callable that empties "fid" in the case that public=True
    unique_recipients = unique_everseen(recipients)

    # Generate payloads and collect urls
    for recipient in unique_recipients:
        payload = None
        endpoint = recipient["endpoint"]
        fid = recipient["fid"]
        public_key = recipient.get("public_key")
        if isinstance(public_key, str):
            public_key = RSA.importKey(public_key)
        protocol = recipient["protocol"]
        public = recipient["public"]

        if protocol == "activitypub":
            if skip_ready_payload["activitypub"]:
                continue
            if entity.__class__.__name__.startswith("Diaspora"):
                # Don't try to do anything with Diaspora entities currently
                skip_ready_payload["activitypub"] = True
                continue
            try:
                if not ready_payloads[protocol]["payload"]:
                    try:
                        # noinspection PyTypeChecker
                        ready_payloads[protocol]["payload"] = handle_create_payload(
                            entity, author_user, protocol, parent_user=parent_user, payload_logger=payload_logger,
                        )
                    except ValueError as ex:
                        # No point continuing for this protocol
                        skip_ready_payload["activitypub"] = True
                        logger.warning("handle_send - skipping activitypub due to failure to generate payload: %s", ex)
                        continue
                payload = copy.copy(ready_payloads[protocol]["payload"])
                if public:
                    payload["to"] = [NAMESPACE_PUBLIC]
                    payload["cc"] = [fid]
                    if isinstance(payload.get("object"), dict):
                        payload["object"]["to"] = [NAMESPACE_PUBLIC]
                        payload["object"]["cc"] = [fid]
                else:
                    payload["to"] = [fid]
                    if isinstance(payload.get("object"), dict):
                        payload["object"]["to"] = [fid]
                rendered_payload = json.dumps(payload).encode("utf-8")
            except Exception:
                logger.error(
                    "handle_send - failed to generate payload for %s, %s: %s", fid, endpoint, traceback.format_exc(),
                    extra={
                        "recipient": recipient,
                        "unique_recipients": list(unique_recipients),
                        "payload": payload,
                        "payloads": payloads,
                        "ready_payloads": ready_payloads,
                        "entity": entity,
                        "author": author_user.id,
                        "parent_user": parent_user.id,
                    }
                )
                continue
            payloads.append({
                "auth": get_http_authentication(author_user.rsa_private_key, f"{author_user.id}#main-key"),
                "payload": rendered_payload,
                "content_type": 'application/ld+json; profile="https://www.w3.org/ns/activitystreams"',
                "urls": {endpoint},
            })
        elif protocol == "diaspora":
            if entity.__class__.__name__.startswith("Activitypub"):
                # Don't try to do anything with Activitypub entities currently
                skip_ready_payload["diaspora"] = True
                continue
            if public:
                if skip_ready_payload["diaspora"]:
                    continue
                if public_key:
                    logger.warning("handle_send - Diaspora recipient cannot be public and use encrypted delivery")
                    continue
                if not ready_payloads[protocol]["payload"]:
                    try:
                        # noinspection PyTypeChecker
                        ready_payloads[protocol]["payload"] = handle_create_payload(
                            entity, author_user, protocol, parent_user=parent_user, payload_logger=payload_logger,
                        )
                    except Exception as ex:
                        # No point continuing for this protocol
                        skip_ready_payload["diaspora"] = True
                        logger.warning("handle_send - skipping diaspora due to failure to generate payload: %s", ex)
                        continue
                ready_payloads["diaspora"]["urls"].add(endpoint)
            else:
                if not public_key:
                    logger.warning("handle_send - Diaspora recipient cannot be private without a public key for "
                                   "encrypted delivery")
                    continue
                # Private payload
                try:
                    payload = handle_create_payload(
                        entity, author_user, "diaspora", to_user_key=public_key, parent_user=parent_user,
                        payload_logger=payload_logger,
                    )
                    payload = json.dumps(payload)
                except Exception as ex:
                    logger.error("handle_send - failed to generate private payload for %s: %s", endpoint, ex)
                    continue
                payloads.append({
                    "urls": {endpoint}, "payload": payload, "content_type": "application/json", "auth": None,
                })

    # Add public diaspora payload
    if ready_payloads["diaspora"]["payload"]:
        payloads.append({
            "urls": ready_payloads["diaspora"]["urls"], "payload": ready_payloads["diaspora"]["payload"],
            "content_type": "application/magic-envelope+xml", "auth": None,
        })

    logger.debug("handle_send - %s", payloads)

    # Do actual sending
    for payload in payloads:
        for url in payload["urls"]:
            try:
                send_document(
                    url,
                    payload["payload"],
                    auth=payload["auth"],
                    headers={"Content-Type": payload["content_type"]},
                )
            except Exception as ex:
                logger.error("handle_send - failed to send payload to %s: %s, payload: %s", url, ex, payload["payload"])
