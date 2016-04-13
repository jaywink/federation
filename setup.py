#!/usr/bin/env python
from setuptools import setup, find_packages


description = 'Python library for abstracting social federation protocols'


setup(
    name='Social-Federation',
    version='0.3.1',
    description=description,
    long_description=description,
    author='Jason Robinson',
    author_email='mail@jasonrobinson.me',
    maintainer='Jason Robinson',
    maintainer_email='mail@jasonrobinson.me',
    url='https://github.com/jaywink/social-federation',
    download_url='https://github.com/jaywink/social-federation/releases',
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
