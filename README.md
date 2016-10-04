[![Build Status](https://travis-ci.org/jaywink/social-federation.svg?branch=master)](https://travis-ci.org/jaywink/social-federation) [![codecov.io](https://codecov.io/github/jaywink/social-federation/coverage.svg?branch=master)](https://codecov.io/github/jaywink/social-federation?branch=master) [![Code Health](https://landscape.io/github/jaywink/social-federation/master/landscape.svg?style=flat)](https://landscape.io/github/jaywink/social-federation/master) [![Requirements Status](https://requires.io/github/jaywink/social-federation/requirements.svg?branch=master)](https://requires.io/github/jaywink/social-federation/requirements/?branch=master) [![Stories in Ready](https://badge.waffle.io/jaywink/social-federation.png?label=ready&title=Board)](https://waffle.io/jaywink/social-federation)

[![PyPI version](https://badge.fury.io/py/social-federation.svg)](https://pypi.python.org/pypi/Social-Federation)  [![Documentation Status](http://readthedocs.org/projects/social-federation/badge/?version=latest)](http://social-federation.readthedocs.io/en/latest/?badge=latest) [![PyPI downloads](https://img.shields.io/pypi/dm/Social-Federation.svg)](https://pypi.python.org/pypi/Social-Federation) [![PyPI](https://img.shields.io/pypi/pyversions/Social-Federation.svg?maxAge=2592000)](https://pypi.python.org/pypi/Social-Federation) [![PyPI](https://img.shields.io/pypi/l/Social-Federation.svg?maxAge=2592000)](https://pypi.python.org/pypi/Social-Federation)

# Social-Federation

Python library to abstract social web federation protocols like Diaspora.

## Introduction

The aim of Social-Federation is to provide and abstract multiple social web protocols like Diaspora in one package. This way applications can be built to (almost) transparently support many protocols without the app builder having to know everything about those protocols.

While the library does aim to provide an easy way to implement protocols like Diaspora into your application, it will not be a one to one mirror image of said protocols. The idea is to present one unified collection of entities and high level methods to the application to use. Since protocols can support different feature sets or have different ideas on even simple entities like status messages, it would be impossible to model the core entities according to a single protocol.

![](http://social-federation.readthedocs.io/en/latest/_images/generic_diagram.png)

## Status

Currently the library supports a part of the Diaspora protocol with remaining parts being constantly added. See the [Diaspora](http://social-federation.readthedocs.io/en/latest/protocols.html#diaspora) protocol page for support status.

The code base is well tested and in use in several projects. Backward incompatible changes will however be made at this stage still, however those will be clearly documented in changelog entries.

## Additional information

### Installation and requirements

See [installation documentation](http://social-federation.readthedocs.io/en/latest/install.html).

### Usage and API documentation

See [usage documentation](http://social-federation.readthedocs.io/en/latest/usage.html).

### Support and help

See [development and support documentation](http://social-federation.readthedocs.io/en/latest/development.html).

### License

[BSD 3-clause license](https://www.tldrlegal.com/l/bsd3)

### Author

Jason Robinson / https://jasonrobinson.me / https://github.com/jaywink
