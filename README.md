[![issue tracker](https://img.shields.io/badge/issue%20tracker-codeberg-orange.svg)](https://codeberg.org/socialhome/federation/issues)

[![PyPI version](https://badge.fury.io/py/federation.svg)](https://pypi.python.org/pypi/federation)  [![Documentation Status](http://readthedocs.org/projects/federation/badge/?version=latest)](http://federation.readthedocs.io/en/latest/?badge=latest) [![PyPI](https://img.shields.io/pypi/pyversions/federation.svg?maxAge=2592000)](https://pypi.python.org/pypi/federation) [![PyPI](https://img.shields.io/pypi/l/federation.svg?maxAge=2592000)](https://pypi.python.org/pypi/federation)

# federation

Python library to abstract social web federation protocols like ActivityPub, Diaspora and Matrix.

## Introduction

The aim of `federation` is to provide and abstract multiple social web protocols like 
ActivityPub, Diaspora and Matrix in one package, over an easy to use and understand Python API. 
This way applications can be built to (almost) transparently support many protocols 
without the app builder having to know everything about those protocols.

![](./docs/_static/generic_diagram.png)

## Status

Currently, three protocols are being focused on.

* Diaspora is considered to be stable with most of the protocol implemented.
* ActivityPub is considered to be stable with working federation with most ActivityPub platforms.
* Matrix support is in early phase and not to be considered useful yet.

The code base is well tested and in use in several projects. Backward incompatible changes 
will be clearly documented in changelog entries.

## Additional information

### Installation and requirements

See [installation documentation](http://federation.readthedocs.io/en/latest/install.html).

### Usage and API documentation

See [usage documentation](http://federation.readthedocs.io/en/latest/usage.html).

### Support and help

See [development and support documentation](http://federation.readthedocs.io/en/latest/development.html).

### License

[BSD 3-clause license](https://www.tldrlegal.com/l/bsd3)
