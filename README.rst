==============================================
Francis: Todoist cli with taskwarrior likeness
==============================================

* Free software: MIT License
* Documentation: this README and "francis --help"


Features
========

* view today, tomorrow and other due dates (today, tomorrow, list)
* view specific tasks (show)
* add new tasks (add)
* add a task and mark it as complete (log)
* modify priority, project and due date for tasks (modify)
* mark items as complete (done)
* push off anything due today until tomorrow (deferall)
* see the upcoming week of uncompleted tasks (thisweek)
* see the last week of completed items (timesheet)


Install
=======

Install from git clone because it's not on PyPI, yet:

1. Clone the git repository to your local machine::

     $ git clone https://github.com/willkg/francis

2. Cnstall it with `pipsi <https://github.com/mitsuhiko/pipsi/>`_::

     $ pipsi install .


Usage
=====

View help::

  $ francis --help


Add todo items::

  # Add an item "new item" in the Inbox project due today
  $ francis add new item

  # Add a high priority item "new item" in the work project due today
  $ francis add proj:Work pri:H new item

  # Add an item that has punctuation
  $ francis add "gotta make $$$!"

  # Add an item with quotes
  $ francis add "gotta make them \"happy\""


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


Show this week's timesheet (things you completed)::

  $ francis timesheet


Note: For ids, you can always do suffixes rather than use the whole id which
is pretty unwieldy. For example, if you have an item with id 1234567 you could
refer to it as "567". Generally 3 digits is probably sufficient. If it's not,
francis will whine at you.

To see other commands, do::

  $ francis --help


For development
===============

We're using pytest for tests. To run tests::

  $ make test


Credits
=======

This package was created with Cookiecutter_ and the
`audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
