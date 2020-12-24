Usage
=====


Entities
--------

Federation has it's own base entity classes. When incoming messages are processed, the
protocol specific entity mappers transform the messages into our base entities. In
reverse, when creating outgoing payloads, outgoing protocol specific messages are
constructed from the base entities.

Entity types are as follows below.

.. autoclass:: federation.entities.base.Comment
.. autoclass:: federation.entities.base.Follow
.. autoclass:: federation.entities.base.Image
.. autoclass:: federation.entities.base.Post
.. autoclass:: federation.entities.base.Profile
.. autoclass:: federation.entities.base.Reaction
.. autoclass:: federation.entities.base.Relationship
.. autoclass:: federation.entities.base.Retraction
.. autoclass:: federation.entities.base.Share

Protocol entities
.................

Each protocol additionally has it's own variants of the base entities, for example
Diaspora entities in ``federation.entities.diaspora.entities``. All the protocol
specific entities subclass the base entities so you can safely work with for example
``DiasporaPost`` and use ``isinstance(obj, Post)``.

When creating incoming objects from messages, protocol specific entity classes are
returned. This is to ensure protocol specific extra attributes or methods are
passed back to the caller.

For sending messages out, either base or protocol specific entities can be passed
to the outbound senders.

If you need the correct protocol speficic entity class from the base entity,
each protocol will define a ``get_outbound_entity`` function.

.. autofunction:: federation.entities.activitypub.mappers.get_outbound_entity
.. autofunction:: federation.entities.diaspora.mappers.get_outbound_entity

Federation identifiers
......................

All entities have an ``id`` to guarantee them a unique name in the network.
The format of the ``id`` depends on the protocol in question.

* ActivityPub: maps to the object ``id`` (whether wrapped in an Activity or not)
* Diaspora: maps to ``guid`` for the entity.

Profiles
++++++++

Profiles are uniquely identified by the ``id`` as above. Additionally for Diaspora they always have a ``handle``.
ActivityPub profiles can also have a ``handle`` but it is optional.

A handle will always be in email like format, without the `@` prefix found on some platforms. This will be added
to outgoing payloads where needed.

Creator and owner identifiers
.............................

All entities except ``Profile`` have an ``actor_id`` which tells who created this object or activity. The format
depends on the protocol
in question.

* ActivityPub: maps to Object ``attributedTo`` or Activity ``actor_id``.
* Diaspora: maps to entity ``author``

Activity identifiers
....................

Entities which are an activity on something, for example creating, updating, deleting, following, etc, should have
an ``activity_id`` given to be able to send out to the ActivityPub protocol.

Mentions
........

Entities store mentions in the list ``_mentions``. The list is a simple list of strings which will be either
an URL format ``profile.id`` or handle, as per above examples.

The syntax for a mention in text is URL format ``@{<profile.id>}`` or ``@{<profile.handle>}``.
The GUID format ``profile.id`` cannot be used for a mention.

Examples:

::

    # profile.handle
    Hello @{user@domain.tld}!

    # profile.id in URL format
    Hello @{https://domain.tld/user}

It is suggested ``profile.handle`` syntax is used always for textual mentions unless handles are not available.

Inbound
+++++++

Mentions are added to the entity ``_mentions`` list when processing inbound entities. For ActivityPub they will be
extracted from ``Mention`` tags and for Diaspora extracted from the text using the Diaspora mention format.

Outbound
++++++++

Mentions can be given in the ``_mentions`` list. If not given, they will be extracted from the textual content
using the above formats in the example.

For ActivityPub they will be added as ``Mention`` tags before sending. If the mention is in handle format,
a WebFinger fetch will be made to find the profile URL format ID.

For Diaspora they will be added to the text
in the correct format, if not found. If they are found in the text in non-Diaspora format, they will be converted
before sending.

Discovery
---------

Federation provides many generators to allow providing discovery documents.
They have been made as Pythonic as possible so that library users don't have to
meddle with the various documents and their internals.

The protocols themselves are too complex to document within this library,
please consult protocol documentation on what kind of discovery documents are expected to
be served by the application.

Generators
..........

Helper methods
++++++++++++++

.. autofunction:: federation.hostmeta.fetchers.fetch_nodeinfo_document
.. autofunction:: federation.hostmeta.fetchers.fetch_nodeinfo2_document
.. autofunction:: federation.hostmeta.fetchers.fetch_statisticsjson_document
.. autofunction:: federation.hostmeta.generators.generate_host_meta
.. autofunction:: federation.hostmeta.generators.generate_legacy_webfinger
.. autofunction:: federation.hostmeta.generators.generate_hcard
.. autofunction:: federation.hostmeta.generators.generate_nodeinfo2_document
.. autofunction:: federation.hostmeta.generators.get_nodeinfo_well_known_document

Generator classes
+++++++++++++++++

.. autoclass:: federation.hostmeta.generators.DiasporaHostMeta
.. autoclass:: federation.hostmeta.generators.DiasporaWebFinger
.. autoclass:: federation.hostmeta.generators.DiasporaHCard
.. autoclass:: federation.hostmeta.generators.MatrixClientWellKnown
.. autoclass:: federation.hostmeta.generators.MatrixServerWellKnown
.. autoclass:: federation.hostmeta.generators.NodeInfo
.. autoclass:: federation.hostmeta.generators.RFC7033Webfinger
.. autoclass:: federation.hostmeta.generators.SocialRelayWellKnown

Fetchers
--------

High level utility functions to fetch remote objects. These should be favoured instead of protocol specific utility functions.

.. autofunction:: federation.fetchers.retrieve_remote_content
.. autofunction:: federation.fetchers.retrieve_remote_profile


Inbound
-------

High level utility functions to pass incoming messages to. These should be favoured
instead of protocol specific utility functions.


.. autofunction:: federation.inbound.handle_receive


Outbound
--------

High level utility functions to pass outbound entities to. These should be favoured instead of protocol specific utility functions.

.. autofunction:: federation.outbound.handle_send

Django
------

Some ready provided views and URL configuration exist for Django.

Note! Django is not part of the normal requirements for this library.
It must be installed separately.

.. autofunction:: federation.entities.activitypub.django.views.activitypub_object_view
.. autofunction:: federation.hostmeta.django.generators.rfc7033_webfinger_view
.. autofunction:: federation.hostmeta.django.generators.matrix_client_wellknown_view
.. autofunction:: federation.hostmeta.django.generators.matrix_server_wellknown_view
.. autofunction:: federation.hostmeta.django.generators.nodeinfo2_view

.. _usage-configuration:

Configuration
.............

To use the Django views, ensure a modern version of Django is installed and add the views to your URL config for example as follows. The URL's must be mounted on root if Diaspora protocol support is required.

::

    url(r"", include("federation.hostmeta.django.urls")),

Some settings need to be set in Django settings. An example is below:

::

    FEDERATION = {
        "base_url": "https://myserver.domain.tld,
        "get_object_function": "myproject.utils.get_object",
        "get_private_key_function": "myproject.utils.get_private_key",
        "get_profile_function": "myproject.utils.get_profile",
        "matrix_config_function": "myproject.utils.matrix_config_funct",
        "nodeinfo2_function": "myproject.utils.get_nodeinfo2_data",
        "process_payload_function": "myproject.utils.process_payload",
        "search_path": "/search/?q=",
        "tags_path": "/tags/:tag:",
    }

* ``base_url`` is the base URL of the server, ie protocol://domain.tld.
* ``get_object_function`` should be the full path to a function that will return the object matching the ActivityPub ID for the request object passed to this function.
* ``get_private_key_function`` should be the full path to a function that will accept a federation ID (url, handle or guid) and return the private key of the user (as an RSA object). Required for example to sign outbound messages in some cases.
* ``get_profile_function`` should be the full path to a function that should return a ``Profile`` entity. The function should take one or more keyword arguments: ``fid``, ``handle``, ``guid`` or ``request``. It should look up a profile with one or more of the provided parameters.
* ``matrix_config_function`` (optional) function that returns a Matrix configuration dictionary, with the following objects:

::

    {
      # Location of the homeserver (not server name)
      "homeserver_base_url": "https://matrix.domain.tld",
      # Homeserver domain and port (not server domain)
      "homeserver_domain_with_port": "matrix.domain.tld:443",
      # Homeserver name
      "homeserver_name": "domain.tld",
      # Appservice details
      "appservice": {
        # Unique ID to register with at the homeserver. Don't change this after creating.
        "id": "uniqueid",
        # Short code (a-z only), used for various things like namespacing
        "shortcode": "federatedapp",
        # Secret token for communication
        "token": "secret_token",
      },
      # (Optional) location of identity server
      "identity_server_base_url": "https://id.domain.tld",
      # (Optional) other keys to include in the client well-known (must be a dictionary)
      "client_wellknown_other_keys": {
        "org.foo.key" "barfoo",
      },
      # (Optional) registration shared secret
      "registration_shared_secret": "supersecretstring",
    }

* ``nodeinfo2_function`` (optional) function that returns data for generating a `NodeInfo2 document <https://github.com/jaywink/nodeinfo2>`_. Once configured the path ``/.well-known/x-nodeinfo2`` will automatically generate a NodeInfo2 document. The function should return a ``dict`` corresponding to the NodeInfo2 schema, with the following minimum items:

::

    {server:
        baseUrl
        name
        software
        version
    }
    openRegistrations

* ``process_payload_function`` (optional) function that takes in a request object. It should return ``True`` if successful (or placed in queue for processing later) or ``False`` in case of any errors.
* ``search_path`` (optional) site search path which ends in a parameter for search input, for example "/search?q="
* ``tags_path`` (optional) path format to view items for a particular tag. ``:tag:`` will be replaced with the tag (without ``#``).

Protocols
---------

The code for opening and creating protocol messages lives under each protocol module in ``federation.protocols``.

Each protocol defines a ``protocol.Protocol`` class under it's own module. This is expected to contain certain methods that are used by the higher level functions that are called on incoming messages and when sending outbound messages. Everything that is needed to transform an entity into a message payload and vice versa should be here.

Instead of calling methods directly for a specific protocol, higher level generic functions should be normally used.


Utils
-----

Various utils are provided for internal and external usage.

ActivityPub
...........

.. autofunction:: federation.utils.activitypub.retrieve_and_parse_content
.. autofunction:: federation.utils.activitypub.retrieve_and_parse_document
.. autofunction:: federation.utils.activitypub.retrieve_and_parse_profile

Diaspora
........

.. autofunction:: federation.utils.diaspora.fetch_public_key
.. autofunction:: federation.utils.diaspora.generate_diaspora_profile_id
.. autofunction:: federation.utils.diaspora.get_fetch_content_endpoint
.. autofunction:: federation.utils.diaspora.get_private_endpoint
.. autofunction:: federation.utils.diaspora.get_public_endpoint
.. autofunction:: federation.utils.diaspora.parse_diaspora_uri
.. autofunction:: federation.utils.diaspora.parse_profile_diaspora_id
.. autofunction:: federation.utils.diaspora.parse_profile_from_hcard
.. autofunction:: federation.utils.diaspora.retrieve_and_parse_content
.. autofunction:: federation.utils.diaspora.retrieve_and_parse_diaspora_webfinger
.. autofunction:: federation.utils.diaspora.retrieve_and_parse_profile
.. autofunction:: federation.utils.diaspora.retrieve_diaspora_hcard
.. autofunction:: federation.utils.diaspora.retrieve_diaspora_host_meta

Matrix
......

.. autofunction:: federation.utils.matrix.register_dendrite_user

Network
.......

.. autofunction:: federation.utils.network.fetch_document
.. autofunction:: federation.utils.network.send_document

Protocols
.........

.. autofunction:: federation.utils.protocols.identify_recipient_protocol

Exceptions
----------

Various custom exception classes might be returned.

.. autoexception:: federation.exceptions.EncryptedMessageError
.. autoexception:: federation.exceptions.NoSenderKeyFoundError
.. autoexception:: federation.exceptions.NoSuitableProtocolFoundError
.. autoexception:: federation.exceptions.SignatureVerificationError
