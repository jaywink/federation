[![Build Status](https://travis-ci.org/jaywink/federation.svg?branch=master)](https://travis-ci.org/jaywink/federation) [![codecov.io](https://codecov.io/github/jaywink/federation/coverage.svg?branch=master)](https://codecov.io/github/jaywink/federation?branch=master) [![Code Health](https://landscape.io/github/jaywink/federation/master/landscape.svg?style=flat)](https://landscape.io/github/jaywink/federation/master)

[![PyPI version](https://badge.fury.io/py/federation.svg)](https://pypi.python.org/pypi/federation)  [![Documentation Status](http://readthedocs.org/projects/federation/badge/?version=latest)](http://federation.readthedocs.io/en/latest/?badge=latest) [![PyPI](https://img.shields.io/pypi/pyversions/federation.svg?maxAge=2592000)](https://pypi.python.org/pypi/federation) [![PyPI](https://img.shields.io/pypi/l/federation.svg?maxAge=2592000)](https://pypi.python.org/pypi/federation)

# federation

Python library to abstract social web federation protocols like Diaspora and ActivityPub.

## Introduction

The aim of `federation` is to provide and abstract multiple social web protocols like Diaspora and ActivityPub in one package. This way applications can be built to (almost) transparently support many protocols without the app builder having to know everything about those protocols.

While the library does aim to provide an easy way to implement protocols like Diaspora into your application, it will not be a one to one mirror image of said protocols. The idea is to present one unified collection of entities and high level methods to the application to use. Since protocols can support different feature sets or have different ideas on even simple entities like status messages, it would be impossible to model the core entities according to a single protocol.

![](http://federation.readthedocs.io/en/latest/_images/generic_diagram.png)

## Status

Currently two protocols are being focused on. Diaspora is considered in relatively stable status with most of the protocol implemented. ActivityPub support is work in progress.

The code base is well tested and in use in several projects. Backward incompatible changes will however be made at this stage still, however those will be clearly documented in changelog entries.

## Additional information

### Installation and requirements

See [installation documentation](http://federation.readthedocs.io/en/latest/install.html).

### Usage and API documentation

See [usage documentation](http://federation.readthedocs.io/en/latest/usage.html).

### Support and help

See [development and support documentation](http://federation.readthedocs.io/en/latest/development.html).

### License

[BSD 3-clause license](https://www.tldrlegal.com/l/bsd3)

### Author

Jason Robinson / https://jasonrobinson.me / https://git.feneas.org/jaywink / https://github.com/jaywink 
