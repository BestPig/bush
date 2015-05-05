#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

if sys.version_info < (3, 3, 0):
    from datetime import datetime
    sys.stdout.write("It's %d. This requires Python > 3.3.\n"
                     % datetime.now().year)
    sys.exit(1)

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import bush.meta

readme = open('README.md').read()
requirements = open('requirements.txt').read()

setup(
    name='bush',
    description='A simple naive way to share files.',
    long_description=readme,
    version=bush.meta.__version__,
    author=bush.meta.__author__,
    author_email=bush.meta.__email__,
    url='https://github.com/BestPig/bush',
    license="MIT",
    zip_safe=False,
    keywords='bush',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
    ],

    scripts=['bin/bush'],
    packages=['bush'],
    package_dir={'bush': 'bush'},
    package_data={'bush': ['config.yaml']},

    install_requires=requirements,
)
