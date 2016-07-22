#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup
from setuptools.command.test import test as TestCommand


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest
        pytest.main(self.test_args)


def get_file(fn):
    with open(fn) as fp:
        return fp.read()

requirements = [
    'click',
    'pendulum',
    'tabulate',
    'todoist-python',
]

test_requirements = [
    'pytest',
]

setup(
    name='francis',
    version='0.1.0',
    description='Todoist cli with taskwarrior likeness',
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
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],
    cmdclass={'test': PyTest},
    tests_require=test_requirements
)
