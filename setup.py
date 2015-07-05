#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='Social-Federation',
    version='0.1.0',
    description='Python library for abstracting social federation protocols',
    author='Jason Robinson',
    author_email='mail@jasonrobinson.me',
    url='https://github.com/jaywink/social-federation',
    packages=find_packages(exclude=["*.tests.*", "*.tests"]),
    license="BSD 3-clause",
    install_requires=[
        "Flask==0.10.1",
        "hiredis==0.2.0",
        "redis==2.10.3",
    ],
)
