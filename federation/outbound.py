from federation.entities.diaspora.mappers import get_outbound_entity
from federation.protocols.diaspora.protocol import Protocol
from federation.utils.diaspora import get_public_endpoint
from federation.utils.network import send_document


def handle_create_payload(entity, author_user, to_user=None, parent_user=None):
    """Create a payload with the correct protocol.

    Any given user arguments must have ``private_key`` and ``handle`` attributes.

    :arg entity: Entity object to send. Can be a base entity or a protocol specific one.
    :arg author_user: User authoring the object.
    :arg to_user: Profile entry to send to (required for non-public content)
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
    data = protocol.build_send(entity=outbound_entity, from_user=send_as_user, to_user=to_user)
    return data


def handle_send(entity, author_user, recipients=None, parent_user=None):
    """Send an entity to remote servers.

    Using this we will build a list of payloads per protocol, after resolving any that need to be guessed or
    looked up over the network. After that, each recipient will get the generated protocol payload delivered.

    NOTE! This will not (yet) support Diaspora limited messages - `handle_create_payload` above should be directly
    called instead and payload sent with `federation.utils.network.send_document`.

    Any given user arguments must have ``private_key`` and ``handle`` attributes.

    :arg entity: Entity object to send. Can be a base entity or a protocol specific one.
    :arg author_user: User authoring the object.
    :arg recipients: A list of tuples to delivery to. Tuple contains (recipient handle or domain, protocol or None).
                     For example ``[("foo@example.com", "diaspora"), ("bar@example.com", None)]``.
    :arg parent_user: (Optional) User object of the parent object, if there is one. This must be given for the
                      Diaspora protocol if a parent object exists, so that a proper ``parent_author_signature`` can
                      be generated. If given, the payload will be sent as this user.
    """
    payloads = {"diaspora": {"payload": None, "recipients": set()}}
    # Generate payload per protocol and split recipients to protocols
    for recipient, protocol in recipients:
        # TODO currently we only support Diaspora protocol, so no need to guess, just generate the payload
        if not payloads["diaspora"]["payload"]:
            payloads["diaspora"]["payload"] = handle_create_payload(entity, author_user, parent_user=parent_user)
        if "@" in recipient:
            payloads["diaspora"]["recipients"].add(recipient.split("@")[1])
        else:
            payloads["diaspora"]["recipients"].add(recipient)
    # Do actual sending
    for protocol, data in payloads.items():
        for recipient in data.get("recipients"):
            # TODO protocol independant url generation by importing named helper under protocol
            url = get_public_endpoint(recipient)
            send_document(url, data.get("payload"))
