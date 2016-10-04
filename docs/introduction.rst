Introduction
============

The aim of Social-Federation is to provide and abstract multiple social web protocols like Diaspora in one package. This way applications can be built to (almost) transparently support many protocols without the app builder having to know everything about those protocols.

While the library does aim to provide an easy way to implement protocols like Diaspora into your application, it will not be a one to one mirror image of said protocols. The idea is to present one unified collection of entities and high level methods to the application to use. Since protocols can support different feature sets or have different ideas on even simple entities like status messages, it would be impossible to model the core entities according to a single protocol.

.. image:: _static/generic_diagram.png

Status
------

Currently the library supports a part of the Diaspora protocol with remaining parts being constantly added. See the `Diaspora <http://social-federation.readthedocs.io/en/latest/protocols.html#diaspora>`_ protocol page for support status.

The code base is well tested and in use in several projects. Backward incompatible changes will however be made at this stage still, however those will be clearly documented in changelog entries.

Additional information
----------------------

Installation and requirements
.............................

See `installation documentation <http://social-federation.readthedocs.io/en/latest/install.html>`_.

Usage and API documentation
...........................

See `usage documentation <http://social-federation.readthedocs.io/en/latest/usage.html>`_.

Support and help
................

See `development and support documentation <http://social-federation.readthedocs.io/en/latest/development.html>`_.

License
.......

`BSD 3-clause license <https://www.tldrlegal.com/l/bsd3>`_.

Author
......

Jason Robinson / `jasonrobinson.me <https://jasonrobinson.me>`_ / `GitHub <https://github.com/jaywink>`_

