#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup


def get_file(fn):
    with open(fn) as fp:
        return fp.read()

requirements = [
    'click',
    'tabulate',
    'todoist-python',
]

test_requirements = [
    # TODO: put package test requirements here
]

setup(
    name='francis',
    version='0.1.0',
    description="Todoist cli",
    long_description=(
        get_file('README.rst') + '\n\n' + get_file('HISTORY.rst')
    ),
    author="Will Kahn-Greene",
    author_email='willkg@bluesock.org',
    url='https://github.com/willkg/francis',
    packages=[
        'francis',
    ],
    package_dir={
        'francis': 'francis'
    },
    include_package_data=True,
    install_requires=requirements,
    license="BSD",
    zip_safe=False,
    keywords='todoist cli',
    entry_points="""
        [console_scripts]
        francis=francis.cmdline:click_run
    """,
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    test_suite='tests',
    tests_require=test_requirements
)
