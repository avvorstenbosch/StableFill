#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The setup script."""

from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

with open('changelog.md') as history_file:
    history = history_file.read()

requirements = [
]

setup_requirements = [
]

test_requirements = []

setup(
    author       = "Mauricio Cáceres Bravo",
    author_email = 'mauricio_caceres_bravo@brown.edu',
    classifiers  = [
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
    ],
    description  = "StableFill updates LaTeX, Markdown, and LyX tables and inline values.",
    entry_points = {
        'console_scripts': [
            'stablefill = stablefill:main',
            'tablefill = stablefill:main',
        ]
    },
    extras_require                = {'numpy': ['numpy']},
    install_requires              = requirements,
    license                       = "MIT license",
    long_description              = readme + '\n\n' + history,
    long_description_content_type = 'text/markdown',
    keywords                      = 'stablefill tablefill latex markdown lyx tables',
    name                          = 'stablefill',
    packages                      = find_packages(include = ['stablefill', 'tablefill', 'tablefill.*']),
    python_requires               = '>=3.8',
    setup_requires                = setup_requirements,
    test_suite                    = 'tests',
    tests_require                 = test_requirements,
    url                           = 'https://github.com/avvorstenbosch/StableFill',
    version                       = '0.11.0',
    zip_safe                      = False,
)
