#!/usr/bin/env python
# -*- coding: utf-8 -*-
from ez_setup import use_setuptools
use_setuptools()

from setuptools import setup
from libdoc import __version__
setup(
    name="LibDoc",
    url="http://codesys.com",
    author="3S-Smart Software Solutions GmbH",
    author_email="info@codesys.com",
    description="LibDoc -- CODESYS LibDoc Scripting Collection",
    version=__version__,
    packages=['libdoc'],
    include_package_data=True,
    install_requires=['sphinx', 'docopt', 'unidecode', 'pytz', 'babel', 'polib'],
    entry_points={'console_scripts': ['libdoc=libdoc.__main__:main']},
)