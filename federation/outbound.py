from federation.entities.diaspora.mappers import get_outbound_entity
from federation.protocols.diaspora.protocol import Protocol
from federation.utils.diaspora import get_public_endpoint, get_private_endpoint
from federation.utils.network import send_document


def handle_create_payload(entity, author_user, to_user_key=None, parent_user=None):
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


def handle_send(entity, author_user, recipients=None, parent_user=None):
    """Send an entity to remote servers.

    Using this we will build a list of payloads per protocol, after resolving any that need to be guessed or
    looked up over the network. After that, each recipient will get the generated protocol payload delivered.

    Any given user arguments must have ``private_key`` and ``handle`` attributes.

    :arg entity: Entity object to send. Can be a base entity or a protocol specific one.
    :arg author_user: User authoring the object.
    :arg recipients: A list of recipients to delivery to. Each recipient is a tuple
                     containing at minimum the "id", optionally "public key" for private deliveries.
                     Instead of a tuple, for public deliveries the "id" as str is also ok.
                     If public key is provided, Diaspora protocol delivery will be made as an encrypted
                     private delivery.
                     For example
                     [
                         ("diaspora://user@domain.tld/profile/zyx", <RSAPublicKey object>),
                         ("diaspora://user@domain2.tld/profile/xyz", None),
                         "diaspora://user@domain3.tld/profile/xyz",
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
            payload = handle_create_payload(entity, author_user, to_user_key=public_key, parent_user=parent_user)
            # TODO get_private_endpoint should be imported per protocol
            url = get_private_endpoint(id)
            payloads.append({
                "urls": {url}, "payload": payload,
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
        })

    # Do actual sending
    for payload in payloads:
        for url in payload["urls"]:
            # TODO set content type per protocol above when collecting and use here
            send_document(url, payload["payload"])
