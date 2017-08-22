Protocols
=========

.. _diaspora:

Diaspora
--------

Currently the library supports a part of the protocol with remaining parts being constantly added.

Note! Diaspora project is currently rewriting parts of the protocol. This library aims to support the `new version <http://diaspora.github.io/diaspora_federation/>`_. When possible, compatibility will be kept with the current and legacy versions but this is not the main objective.

The feature set supported by this release is approximately the following:

* WebFinger, hCard and other discovery documents
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

Implementation unfortunately currently requires knowledge of how Diaspora discovery works as the implementer has to implement all the necessary views correctly (even though this library provides document generators). However, the magic envelope, signature and entity building is all abstracted inside the library.

For example implementations in real life projects check :ref:`example-projects`.
