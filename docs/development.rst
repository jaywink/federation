Development
===========

Help is more than welcome to extend this library. Please see the following resources.

* `Source code repo <https://codeberg.org/socialhome/federation>`_
* `Issue tracker <https://codeberg.org/socialhome/federation/issues>`_

NOTE! Due to bugs in the GitLab -> Codeberg migration tool, old issues before October 2024 can
only be found in the old [GitLab issue tracker](https://gitlab.com/jaywink/federation/-/issues).

Environment setup
-----------------

Once you have your (Python 3.7+) virtualenv set up, install the development requirements::

   pip install -r dev-requirements.txt

Running tests
-------------

::

   py.test

Building local documentation
----------------------------

::

   cd docs
   make html

Built documentation is available at ``docs/_build/html/index.html``.

Releasing
---------

::

   pip install -U build twine
   python -m build
   python -m twine upload dist/federation-<version>*

Contact for help
----------------

Easiest via Matrix on room ``#socialhome:federator.dev``.

You can also ask questions or give feedback via issues.
