#!/usr/bin/env python
from setuptools import setup, find_packages

from federation import __version__


description = 'Python library for abstracting social federation protocols'


setup(
    name='Social-Federation',
    version=__version__,
    description=description,
    long_description=description,
    author='Jason Robinson',
    author_email='mail@jasonrobinson.me',
    maintainer='Jason Robinson',
    maintainer_email='mail@jasonrobinson.me',
    url='https://github.com/jaywink/social-federation',
    download_url='https://github.com/jaywink/social-federation/releases',
    packages=find_packages(),
    license="BSD 3-clause",
    install_requires=[
        "cssselect>=0.9.2",
        "dirty-validators>=0.3.0, <0.4.0",
        "lxml>=3.4.0, <4.0.0",
        "jsonschema>=2.0.0, <3.0.0",
        "pycrypto>=2.6.0, <3.0.0",
        "python-dateutil>=2.4.0, <3.0.0",
        "python-xrd==0.1",
        "requests>=2.8.0",
    ],
    include_package_data=True,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Communications',
        'Topic :: Internet',
    ],
    keywords='federation diaspora activitypub social',
)
