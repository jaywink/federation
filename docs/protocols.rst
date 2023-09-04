Protocols
=========

Currently three protocols are being focused on.

* Diaspora is considered to be stable with most of the protocol implemented.
* ActivityPub support should be considered as beta - all the basic
  things work and we are fixing incompatibilities as they are identified.
* Matrix support cannot be considered usable as of yet.

For example implementations in real life projects check :ref:`example-projects`.

.. _diaspora:

Diaspora
--------

This library only supports the `current renewed version <http://diaspora.github.io/diaspora_federation/>`_ of the protocol. Compatibility for the legacy version was dropped in version 0.18.0.

The feature set supported is the following:

* Webfinger, hCard and other discovery documents
* NodeInfo 1.0 documents
* Social-Relay documents
* Magic envelopes, signatures and other transport method related necessities
* Entities as follows:

   * Comment
   * Like
   * Photo
   * Profile
   * Retraction
   * StatusMessage
   * Contact
   * Reshare

.. _activitypub:

ActivityPub
-----------

Features currently supported:

* Webfinger
* Objects and activities as follows:

   * Actor (Person outbound, Person, Organization, Service inbound)
   * Note, Article and Page (Create, Delete, Update)
     * These become a ``Post`` or ``Comment`` depending on ``inReplyTo``.
   * Attachment images, (inbound only for audios and videos) from the above objects
   * Follow, Accept Follow, Undo Follow
   * Announce
   * Inbound Peertube Video objects translated as ``Post``.
     
* Inbound processing of reply collections, for platforms that implement it.
* Link, Like, View, Signature, PropertyValue, IdentityProof and Emojis objects are only processed for inbound
  payloads currently. Outbound processing requires support by the client
  application.

Namespace
.........

All payloads over ActivityPub sent can be identified with by checking ``@context`` which will include the ``pyfed: https://docs.jasonrobinson.me/ns/python-federation`` namespace.

Content media type
..................

The following keys will be set on the entity based on the ``source`` property existing:

* if the object has an ``object.source`` property:
  * ``_media_type`` will be the source media type (only text/markdown is supported).
  * ``rendered_content`` will be the object ``content``
  * ``raw_content`` will be the source ``content``
* if the object has no ``object.source`` property:
  * ``_media_type`` will be ``text/html``
  * ``rendered_content`` will be the object ``content``
  * ``raw_content`` will be empty

The ``contentMap`` property is processed but content language selection is not implemented yet.

For outbound entities, ``raw_content`` is expected to be in ``text/markdown``,
specifically CommonMark. The client applications are expected to provide the
rendered content for protocols that require it (e.g. ActivityPub).
When sending payloads, ``object.contentMap`` will be set to ``rendered_content``
and ``raw_content`` will be added to the ``object.source`` property.

Medias
......

Any images referenced in the ``raw_content`` of outbound entities will be extracted
into ``object.attachment`` object. For receivers that don't support inline images,
image attachments will have a ``pyfed:inlineImage`` property set to ``true`` to
indicate the image has been extracted from the content. Receivers should ignore the
inline image attachments if they support showing ``<img>`` HTML tags or the markdown
content in ``object.source``. Outbound audio and video attachments currently lack  
support from client applications.

For inbound entities we do this automatically by not including received image attachments in
the entity ``_children`` attribute. Audio and video are passed through the client application.

Hashtags and mentions
.....................

For outbound payloads, client applications must add/set the hashtag/mention value to
the ``class`` attribute of rendered content linkified hashtags/mentions. These will be
used to help build the corresponding ``Hashtag`` and ``Mention`` objects.

For inbound payloads, if a markdown source is provided, hashtags/mentions will be extracted
through the same method used for Diaspora. If only HTML content is provided, the ``a`` tags
will be marked with a ``data-[hashtag|mention]`` attribute (based on the provided Hashtag/Mention
objects) to facilitate the ``href`` attribute modifications lient applications might
wish to make. This should ensure links can be replaced regardless of how the HTML is structured.

.. _matrix:

Matrix
------

The aim of Matrix support in this library is not to provide instant messaging but to wrap
the parts of the Matrix protocol that specifically are especially useful for social media
applications. The current ongoing work on `Ceruelan <https://matrix.org/blog/2020/12/18/introducing-cerulean>`_
provides much of what will be implemented in this library.

This library doesn't aim to be a homeserver or provide any part of the server to server API.
The plan is to provide an appservice to hook onto a separate homeserver that deals with all
the complex protocol related details. This library will then aim to abstract much of what the
appservice gives or takes behind the same API as is provided for the other protocols.

Currently support is being added, please visit back in future versions.

NOTE! Current features also assume Django is configured, though this is likely to not be
the case in the future.

Appservice
..........

To generate the appservice registration file you must ensure you've added the relevant
configuration (see :ref:`usage-configuration`).

Then launch a Django shell inside your project and run the following:

::

    from federation.protocols.matrix.appservice import print_registration_yaml
    print_registration_yaml()

This YAML needs to be registered with the linked Matrix homeserver as instructed in the
relevant homeserver documentation.
