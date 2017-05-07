from federation.entities.diaspora.mappers import get_outbound_entity
from federation.protocols.diaspora.protocol import Protocol
from federation.utils.diaspora import get_public_endpoint
from federation.utils.network import send_document


def handle_create_payload(entity, from_user, to_user=None):
    """Create a payload with the correct protocol.

    Since we don't know the protocol, we need to first query the recipient. However, for a PoC implementation,
    supporting only Diaspora, we're going to assume that for now.

    ``from_user`` must have ``private_key`` and ``handle`` attributes.
    ``to_user`` must have ``key`` attribute.

    :arg entity: Entity object to send
    :arg from_user: Profile sending the object
    :arg to_user: Profile entry to send to (required for non-public content)
    :returns: Built payload message (str)
    """
    # Just use Diaspora protocol for now
    protocol = Protocol()
    outbound_entity = get_outbound_entity(entity, from_user.private_key)
    data = protocol.build_send(entity=outbound_entity, from_user=from_user, to_user=to_user)
    return data


def handle_send(entity, from_user, recipients=None):
    """Send an entity to remote servers.

    `from_user` must have `private_key` and `handle` attributes.

    `recipients` should be a list of tuples, containing:
        - recipient handle, domain or id
        - protocol (optional, if known)

    Using this we will build a list of payloads per protocol, after resolving any that need to be guessed or
    looked up over the network. After that, each recipient will get the generated protocol payload delivered.

    NOTE! This will not support Diaspora limited messages - `handle_create_payload` above should be directly
    called instead and payload sent with `federation.utils.network.send_document`.
    """
    payloads = {"diaspora": {"payload": None, "recipients": set()}}
    # Generate payload per protocol and split recipients to protocols
    for recipient, protocol in recipients:
        # TODO currently we only support Diaspora protocol, so no need to guess, just generate the payload
        if not payloads["diaspora"]["payload"]:
            payloads["diaspora"]["payload"] = handle_create_payload(entity, from_user)
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
