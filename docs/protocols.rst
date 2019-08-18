Protocols
=========

Currently two protocols are being focused on. Diaspora is considered in relatively stable status with most of the protocol implemented. ActivityPub support is work in progress.

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

   * Actor (Person)
   * Note, Article and Page (Create, Delete, Update)
     * These become a ``Post`` or ``Comment`` depending on ``inReplyTo``.
   * Attachment images from the above objects
   * Follow, Accept Follow, Undo Follow
   * Announce

Namespace
.........

All payloads over ActivityPub sent can be identified with by checking ``@context`` which will include the ``pyfed: https://docs.jasonrobinson.me/ns/python-federation`` namespace.

Content media type
..................

When receiving, all ``object.content`` keys are expected to be in ``text/html``.

For outbound entities, ``raw_content`` is expected to be in ``text/markdown``, specifically CommonMark. When sending payloads, ``raw_content`` will be rendered via the ``commonmark`` library into ``object.content``. The original ``raw_content`` will be added to the ``object.source`` property.

Images
......

Any images referenced in the ``raw_content`` of outbound entities will be extracted into ``object.attachment`` objects, for receivers that don't support inline images. These attachments will have a ``pyfed:inlineImage`` property set to ``true`` to indicate the image has been extrated from the content. Receivers should ignore the inline image attachments if they support showing ``<img>`` HTML tags or the markdown content in ``object.source``.

For inbound entities we do this automatically by not including received attachments in the entity ``_children`` attribute.
