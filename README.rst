===============================
Francis
===============================

.. image:: https://img.shields.io/pypi/v/francis.svg
        :target: https://pypi.python.org/pypi/francis

.. image:: https://img.shields.io/travis/willkg/francis.svg
        :target: https://travis-ci.org/willkg/francis

.. image:: https://readthedocs.org/projects/francis/badge/?version=latest
        :target: https://readthedocs.org/projects/francis/?badge=latest
        :alt: Documentation Status


Todoist cli

* Free software: ISC license
* Documentation: https://francis.readthedocs.org.


Features
--------

* view today, tomorrow and other date-based todo lists
* modify priority and project
* mark items as complete


Install
-------

Install from git clone because it's not on PyPI, yet:

1. Clone the git repository to your local machine::

     $ git clone https://github.com/willkg/francis

2. Cnstall it with `pipsi <https://github.com/mitsuhiko/pipsi/>`_::

     $ pipsi install .


Usage
-----

View help::

  $ francis --help


View todo items::

  # Shows today's items
  $ francis

  # Shows today's items
  $ francis today

  # Shows overdue items
  $ francis overdue

  # Shows items due July 22nd
  $ francis list "july 22"

  # Shows items due friday
  $ francis list friday


Modify todo items::

  # Change priority to high (4)
  $ francis set 4040404 pri:H

  # Change priority to low (1)
  $ francis set 4040404 pri:L

  # Change project to "Work"
  $ francis set 4040404 proj:work

  # Do both at the same time to multiple tasks
  $ francis set 3030303,4040404,5050505 pri:H proj:work


Show details for specified items::

  # Show one item
  $ francis show 4040404

  # Show multiple items
  $ francis show 3030303,4040404


For ids, you can always do suffixes rather than use the whole id which is
pretty unwieldy. For example, if you have an item with id 1234567 you could
refer to it as "567". Generally 3 digits is probably sufficient. If it's not,
francis will whine at you.


Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
