Introduction
============

The aim of Social-Federation is to provide and abstract multiple social web protocols like Diaspora in one package. This way applications can be built to (almost) transparently support many protocols without the app builder having to know everything about those protocols.

Status
------

Currently the library supports a part of the Diaspora protocol with remaining parts being constantly added. See the :ref:`diaspora` protocol page for support status.

The code base is well tested and in use in several projects. A lot of backward incompatible changes will however be made at this stage still, however those will be clearly documented in changelog entries.

.. _example-projects:

Projects using Social-Federation
--------------------------------

For examples on how to integrate this library into your project, check these examples:

* `Socialhome <https://github.com/jaywink/socialhome>`_ - a federated home page builder slash personal social network server with high emphasis on card style content visualization.
* `Social-Relay <https://github.com/jaywink/social-relay>`_ - a reference server for the public content relay system that uses the Diaspora protocol.
