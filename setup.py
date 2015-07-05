#!/usr/bin/env python
from pip.req import parse_requirements
from setuptools import setup, find_packages


# parse_requirements() returns generator of pip.req.InstallRequirement objects
install_reqs = parse_requirements("requirements.txt")

# reqs is a list of requirement
# e.g. ['django==1.5.1', 'mezzanine==1.4.6']
reqs = [str(ir.req) for ir in install_reqs]


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
    ] + reqs,
)
