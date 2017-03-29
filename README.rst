.. image:: https://travis-ci.org/pglass/sqlitis.svg?branch=master
    :target: https://travis-ci.org/pglass/sqlitis

=========
 sqlitis
=========

This is a tool to convert plain SQL queries to SQLAlchemy expressions. It is usable from the command line or as a library.

This converts to the `SQLAlchemy expression language`_. It does not support the SQLAlchemy ORM.

This library is currently experimental and has not yet been published to PyPI. To try it out, you will need to clone this repo and install it.

.. code-block:: bash

    $ git clone git@github.com:pglass/sqlitis.git
    $ cd sqlitits && pip install .
    $ sqlitis --help

Examples
--------

Turning a select query into a sqlachemy expression:

.. code-block:: bash

    $ sqlitis 'select foo.name, bar.value from foo join bar'
    select([foo.c.name, bar.c.value]).select_from(foo.join(bar))


Converting a join:

.. code-block:: bash

    $ sqlitis 'foo join bar on foo.id = bar.foo_id and (foo.val < 100 or bar.val < 100)'
    foo.join(bar, and_(foo.c.id == bar.c.foo_id, or_(foo.c.val < 100, bar.c.val < 100)))

Running tests
-------------

This repository includes a data-driven test suite as well as style checks (with `flake8`_) and automatic code formatting (with `yapf`_).

Use tox to run the tests.

.. code-block:: bash

    $ pip install tox
    ### Run everything
    $ tox
    ### Run just the unit/functional tests
    $ tox -e py27
    ### Run just style/formatting checks
    $ tox -e flake8

`yapf`_ is used to automatically fix code style/formatting errors. It will reformat your code in place.

.. code-block:: bash

    ### Auto-fix style/formatting checks
    $ tox -e yapf

There are three types of tests:

- Unit tests of the internal models
- Unit tests of the core `to_sqla` function
- Functional tests that execute the generated SQLAlchemy expressions, against a sqlite database.

Most of these tests are generated from data in ``tests/data.json``.

SQL Support Checklist
---------------------

- [ ] Select
    - [x] Star: ``SELECT * FROM foo``
    - [x] Multiple columns: ``SELECT a, b, c FROM foo``
    - [x] Qualified column names: ``SELECT foo.a, foo.b FROM foo``
    - [x] Column aliases: ``SELECT foo.id AS foo_id, foo.name AS foo_name from FOO``
    - [x] Simple join: ``SELECT foo.a, bar.b FROM foo JOIN bar``
    - [x] On Clauses: ``SELECT foo.a, bar.b FROM foo JOIN bar ON foo.id = bar.foo_id``
    - [x] Conjuctions (AND/OR): ``SELECT foo.a, bar.b FROM foo join bar ON foo.id = bar.foo_id AND foo.val > 1``
    - [x] Select from subquery: ``SELECT id FROM (SELECT * FROM foo)``
    - [x] Where: ``SELECT id FROM foo WHERE id = 123``
    - [ ] Between: ``SELECT a FROM foo WHERE foo.val BETWEEN 1 AND 20``
    - [x] Select distinct: ``SELECT DISTINCT a FROM foo``
    - [ ] Aggregate functions (SUM, AVG, COUNT, MIN, MAX): ``SELECT COUNT(*) FROM foo``
    - [ ] Group by: ``SELECT COUNT(*) FROM foo GROUP BY column``
    - [ ] Like
    - [ ] Limit/offset
    - [ ] Order by
    - [ ] Outer join
- [ ] Insert
- [ ] Update
- [ ] Delete

.. _SQLAlchemy expression language: http://docs.sqlalchemy.org/en/latest/core/tutorial.html#sql-expression-language-tutorial
.. _flake8: http://flake8.pycqa.org/en/latest/
.. _yapf: https://github.com/google/yapf
