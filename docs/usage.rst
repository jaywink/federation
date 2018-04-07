Usage
=====


Entities
--------

Federation has it's own base entity classes. When incoming messages are processed, the protocol specific entity mappers transform the messages into our base entities. In reverse, when creating outgoing payloads, outgoing protocol specific messages are constructed from the base entities.

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

Each protocol additionally has it's own variants of the base entities, for example Diaspora entities in ``federation.entities.diaspora.entities``. All the protocol specific entities subclass the base entities so you can safely work with for example ``DiasporaPost`` and use ``isinstance(obj, Post)``.

When creating incoming objects from messages, protocol specific entity classes are returned. This is to ensure protocol specific extra attributes or methods are passed back to the caller.

For sending messages out, either base or protocol specific entities can be passed to the outbound senders. Base entities should be preferred unless the caller knows which protocol to send to.

If you need the correct protocol speficic entity class from the base entity, each protocol will define a ``get_outbound_entity`` function, for example the Diaspora function as follows.

.. autofunction:: federation.entities.diaspora.mappers.get_outbound_entity


Discovery
---------

Federation provides many generators to allow providing the discovery documents that are necessary for the Diaspora protocol for example. The have been made as Pythonic as possible so that library users don't have to meddle with the various documents and their internals.

The protocols themselves are too complex to document within this library, please consult protocol documentation on what kind of discovery documents are expected to be served by the application.

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
.. autofunction:: federation.hostmeta.generators.get_nodeinfo_well_known_document

Generator classes
+++++++++++++++++

.. autoclass:: federation.hostmeta.generators.DiasporaHostMeta
.. autoclass:: federation.hostmeta.generators.DiasporaWebFinger
.. autoclass:: federation.hostmeta.generators.DiasporaHCard
.. autoclass:: federation.hostmeta.generators.NodeInfo
.. autoclass:: federation.hostmeta.generators.RFC3033Webfinger
.. autoclass:: federation.hostmeta.generators.SocialRelayWellKnown

Fetchers
--------

High level utility functions to fetch remote objects. These should be favoured instead of protocol specific utility functions.

.. autofunction:: federation.fetchers.retrieve_remote_content
.. autofunction:: federation.fetchers.retrieve_remote_profile


Inbound
-------

High level utility functions to pass incoming messages to. These should be favoured instead of protocol specific utility functions.


.. autofunction:: federation.inbound.handle_receive


Outbound
--------

High level utility functions to pass outbound entities to. These should be favoured instead of protocol specific utility functions.

.. autofunction:: federation.outbound.handle_create_payload
.. autofunction:: federation.outbound.handle_send

Django
------

Some ready provided views and URL configuration exist for Django.

Note! Django is not part of the normal requirements for this library. It must be installed separately.

.. autofunction:: federation.hostmeta.django.generators.rfc3033_webfinger_view

Configuration
.............

To use the Django views, ensure a modern version of Django is installed and add the views to your URL config for example as follows. The URL's must be mounted on root if Diaspora protocol support is required.

::

    url(r"", include("federation.hostmeta.django.urls")),

Some settings need to be set in Django settings. An example is below:

::

    FEDERATION = {
        "base_url": "https://myserver.domain.tld,
        "get_profile_function": "myproject.utils.get_profile_by_handle",
        "search_path": "/search/?q=",
    }

* ``base_url`` is the base URL of the server, ie protocol://domain.tld.
* ``profile_id_function`` should be the full path to a function that given a handle will return a dictionary with information that will be used to generate the webfinger document. The dict should contain the following elements:

  * ``id`` - Diaspora URI format ID.
  * ``profile_path`` - profile path for generating an absolute URL to the profile page of the user.
  * ``atom_path`` - (optional) atom feed path for the profile

* ``search_path`` (optional) site search path which ends in a parameter for search input, for example "/search?q="

Protocols
---------

The code for opening and creating protocol messages lives under each protocol module in ``federation.protocols``. Currently Diaspora protocol is the only protocol supported.

Each protocol defines a ``protocol.Protocol`` class under it's own module. This is expected to contain certain methods that are used by the higher level functions that are called on incoming messages and when sending outbound messages. Everything that is needed to transform an entity into a message payload and vice versa should be here.

Instead of calling methods directly for a specific protocol, higher level generic functions should be normally used.


Utils
-----

Various utils are provided for internal and external usage.

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
.. autofunction:: federation.utils.diaspora.retrieve_and_parse_profile
.. autofunction:: federation.utils.diaspora.retrieve_diaspora_hcard
.. autofunction:: federation.utils.diaspora.retrieve_diaspora_webfinger
.. autofunction:: federation.utils.diaspora.retrieve_diaspora_host_meta

Network
.......

.. autofunction:: federation.utils.network.fetch_document
.. autofunction:: federation.utils.network.send_document


Exceptions
----------

Various custom exception classes might be returned.

.. autoexception:: federation.exceptions.EncryptedMessageError
.. autoexception:: federation.exceptions.NoSenderKeyFoundError
.. autoexception:: federation.exceptions.NoSuitableProtocolFoundError
.. autoexception:: federation.exceptions.SignatureVerificationError
