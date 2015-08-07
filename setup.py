#!/usr/bin/env python
from setuptools import setup, find_packages


setup(
    name='Social-Federation',
    version='0.1.1',
    description='Python library for abstracting social federation protocols',
    author='Jason Robinson',
    author_email='mail@jasonrobinson.me',
    url='https://github.com/jaywink/social-federation',
    packages=find_packages(exclude=["*.tests.*", "*.tests"]),
    license="BSD 3-clause",
    install_requires=[
        "dirty-validators==0.3.2",
        "lxml==3.4.4",
        "jsonschema==2.5.1",
        "pycrypto==2.6.1",
        "python-dateutil==2.4.2",
        "python-xrd==0.1",
    ],
    test_require=[
        "pytest==2.7.2",
    ],
    include_package_data=True,
)
