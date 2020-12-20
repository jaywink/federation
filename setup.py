#!/usr/bin/env python
import os

from setuptools import setup, find_packages

from federation import __version__


description = 'Python library to abstract social web federation protocols like ActivityPub and Diaspora.'


def get_long_description():
    return open(os.path.join(os.path.dirname(__file__), "docs", "introduction.rst")).read()


setup(
    name='federation',
    version=__version__,
    description=description,
    long_description=get_long_description(),
    author='Jason Robinson',
    author_email='mail@jasonrobinson.me',
    maintainer='Jason Robinson',
    maintainer_email='mail@jasonrobinson.me',
    url='https://git.feneas.org/jaywink/federation',
    download_url='https://pypi.org/project/federation/',
    packages=find_packages(),
    license="BSD 3-clause",
    install_requires=[
        "attrs",
        "bleach>3.0",
        "commonmark",
        "cryptography",
        "cssselect>=0.9.2",
        "dirty-validators>=0.3.0",
        "lxml>=3.4.0",
        "iteration_utilities",
        "jsonschema>=2.0.0",
        "pycryptodome>=3.4.10",
        "python-dateutil>=2.4.0",
        "python-xrd>=0.1",
        "pytz",
        "requests>=2.8.0",
        "requests-http-signature-jaywink>=0.1.0.dev0",
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
        'Programming Language :: Python :: Implementation :: CPython',
        'Topic :: Communications',
        'Topic :: Internet',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='federation diaspora activitypub federate fediverse social',
)
