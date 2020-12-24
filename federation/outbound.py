import copy
import importlib
import json
import logging
import traceback
from typing import List, Dict, Union

# noinspection PyPackageRequirements
from Crypto.PublicKey import RSA
# noinspection PyPackageRequirements
from Crypto.PublicKey.RSA import RsaKey
from iteration_utilities import unique_everseen

from federation.entities.activitypub.constants import NAMESPACE_PUBLIC
from federation.entities.mixins import BaseEntity
from federation.protocols.activitypub.signing import get_http_authentication
from federation.types import UserType
from federation.utils.matrix import get_matrix_configuration
from federation.utils.network import send_document

logger = logging.getLogger("federation")


def handle_create_payload(
        entity: BaseEntity,
        author_user: UserType,
        protocol_name: str,
        to_user_key: RsaKey = None,
        parent_user: UserType = None,
        payload_logger: callable = None,
) -> Union[str, Dict, List[Dict]]:
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

    :returns: Built payload(s) (str or dict or list (of payloads))
    """
    mappers = importlib.import_module(f"federation.entities.{protocol_name}.mappers")
    protocol = importlib.import_module(f"federation.protocols.{protocol_name}.protocol")
    # noinspection PyUnresolvedReferences
    protocol = protocol.Protocol()
    # noinspection PyUnresolvedReferences
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
                        {
                            "endpoint": "https://matrix.domain.tld",
                            "fid": "#@user:domain.tld",
                            "protocol": "matrix",
                            "public": True,
                        }
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
            "headers": {},
            "payload": None,
            "urls": set(),
            "method": None,
        },
        "diaspora": {
            "auth": None,
            "headers": {},
            "payload": None,
            "urls": set(),
            "method": None,
        },
        "matrix": {
            "auth": None,
            "headers": {},
            "payload": None,
            "urls": set(),
            "method": None,
        },
    }
    skip_ready_payload = {
        "activitypub": False,
        "diaspora": False,
        "matrix": False,
    }

    # Flatten to unique recipients
    # TODO supply a callable that empties "fid" in the case that public=True
    unique_recipients = unique_everseen(recipients)

    matrix_config = None

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
            if entity.__class__.__name__.startswith("Diaspora") or entity.__class__.__name__.startswith("Matrix"):
                # Don't try to do anything with these entities currently
                skip_ready_payload["activitypub"] = True
                continue
            # noinspection PyBroadException
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
                    "handle_send - failed to generate activitypub payload for %s, %s: %s",
                    fid, endpoint, traceback.format_exc(),
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
                "headers": {
                    "Content-Type": 'application/ld+json; profile="https://www.w3.org/ns/activitystreams"',
                },
                "payload": rendered_payload,
                "urls": {endpoint},
            })
        elif protocol == "diaspora":
            if entity.__class__.__name__.startswith("Activitypub") or entity.__class__.__name__.startswith("Matrix"):
                # Don't try to do anything with these entities currently
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
                    "auth": None,
                    "headers": {
                        "Content-Type": "application/json",
                    },
                    "payload": payload,
                    "urls": {endpoint},
                })
        elif protocol == "matrix":
            if skip_ready_payload["matrix"]:
                continue
            if entity.__class__.__name__.startswith("Activitypub") or entity.__class__.__name__.startswith("Diaspora"):
                # Don't try to do anything with these entities currently
                skip_ready_payload["matrix"] = True
                continue
            payload_info = []
            # noinspection PyBroadException
            try:
                try:
                    # For matrix we actually might get multiple payloads and endpoints
                    payload_info = handle_create_payload(
                        entity, author_user, protocol, parent_user=parent_user, payload_logger=payload_logger,
                    )
                except ValueError as ex:
                    # No point continuing for this protocol
                    skip_ready_payload["matrix"] = True
                    logger.warning("handle_send - skipping matrix due to failure to generate payload: %s", ex)
                    continue
                if not matrix_config:
                    matrix_config = get_matrix_configuration()
                for payload in payload_info:
                    rendered_payload = json.dumps(payload["payload"]).encode("utf-8")
                    payloads.append({
                        "auth": None,
                        "headers": {
                            "Authorization": f"Bearer {matrix_config['appservice']['token']}",
                            "Content-Type": "application/json",
                        },
                        "payload": rendered_payload,
                        "urls": {payload["endpoint"]},
                        "method": payload["method"],
                    })
            except Exception:
                logger.error(
                    "handle_send - failed to generate matrix payload for %s, %s: %s",
                    fid, endpoint, traceback.format_exc(),
                    extra={
                        "recipient": recipient,
                        "unique_recipients": list(unique_recipients),
                        "payload_info": payload_info,
                        "payloads": payloads,
                        "ready_payloads": ready_payloads,
                        "entity": entity,
                        "author": author_user.id,
                        "parent_user": parent_user.id,
                    }
                )
                continue

    # Add public diaspora payload
    if ready_payloads["diaspora"]["payload"]:
        payloads.append({
            "auth": None,
            "headers": {
                "Content-Type": "application/magic-envelope+xml",
            },
            "payload": ready_payloads["diaspora"]["payload"],
            "urls": ready_payloads["diaspora"]["urls"],
        })

    logger.debug("handle_send - %s", payloads)

    # Do actual sending
    for payload in payloads:
        for url in payload["urls"]:
            try:
                # TODO send_document and fetch_document need to handle rate limits
                send_document(
                    url,
                    payload["payload"],
                    auth=payload["auth"],
                    headers=payload["headers"],
                    method=payload["method"],
                )
            except Exception as ex:
                logger.error("handle_send - failed to send payload to %s: %s, payload: %s", url, ex, payload["payload"])
