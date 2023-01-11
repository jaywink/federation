#!/usr/bin/env python
import os

from setuptools import setup, find_packages

from federation import __version__


description = 'Python library to abstract social web federation protocols like ActivityPub, Matrix and Diaspora.'


def get_long_description():
    return open(os.path.join(os.path.dirname(__file__), "docs", "introduction.rst")).read()


setup(
    name='federation',
    version=__version__,
    description=description,
    dependency_links=[
        "https://github.com/tripougnif/python-httpsig-socialhome/tarball/master#egg=f04c890ecca4d8921cd838a96db3e3345a80b4f0-0.1"
    ],
    long_description=get_long_description(),
    author='Jason Robinson',
    author_email='mail@jasonrobinson.me',
    maintainer='Jason Robinson',
    maintainer_email='mail@jasonrobinson.me',
    url='https://gitlab.com/jaywink/federation',
    download_url='https://pypi.org/project/federation/',
    packages=find_packages(),
    license="BSD 3-clause",
    install_requires=[
        "attrs",
        "bleach>3.0",
        "calamus",
        "commonmark",
        "cryptography",
        "cssselect>=0.9.2",
        "dirty-validators>=0.3.0",
        "lxml>=3.4.0",
        "iteration_utilities",
        "jsonschema>=2.0.0",
        "pycryptodome>=3.4.10",
        "python-dateutil>=2.4.0",
        "python-magic",
        "python-slugify>=5.0.0",
        "python-xrd>=0.1",
        "pytz",
        "PyYAML",
        "redis",
        "requests>=2.8.0",
        "requests-cache",
        "f04c890ecca4d8921cd838a96db3e3345a80b4f0-0.1",
    ],
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Communications',
        'Topic :: Internet',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='federation diaspora activitypub matrix protocols federate fediverse social',
)
