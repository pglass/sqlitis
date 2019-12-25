[![Build Status](https://travis-ci.org/pglass/sqlitis.svg?branch=master)](https://travis-ci.org/pglass/sqlitis)
[![PyPI](https://img.shields.io/pypi/v/sqlitis)](https://pypi.python.org/pypi/sqlitis)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/sqlitis)](https://pypi.python.org/pypi/sqlitis)

Overview
--------

Sqlitis is a tool to convert plain SQL queries to SQLAlchemy expressions. It is usable from the command line or as a library.

Sqlitis converts to the [SQLAlchemy expression language](http://docs.sqlalchemy.org/en/latest/core/tutorial.html#sql-expression-language-tutorial). It does not support the SQLAlchemy ORM.

```bash
$ pip install sqlitis
```

Examples
--------

Turning a select query into a sqlachemy expression:

```bash
$ sqlitis 'select foo.name, bar.value from foo join bar'
select([foo.c.name, bar.c.value]).select_from(foo.join(bar))
```

Converting a join:

```bash
$ sqlitis 'foo join bar on foo.id = bar.foo_id and (foo.val < 100 or bar.val < 100)'
foo.join(bar, and_(foo.c.id == bar.c.foo_id, or_(foo.c.val < 100, bar.c.val < 100)))
```

Running tests
-------------

Use tox to run the tests.

```bash
$ pip install tox

### Run everything
$ tox

### Run the unit/functional tests
$ tox -e py36

### Run style checks
$ tox -e flake8 black
```

The code is formatted using [black](https://pypi.org/project/black/).

```bash
### Reformat the code with black
$ make format

### Check if black needs to be run. This does not reformat.
$ tox -e black
```

There are three types of tests:

- Unit tests of the internal model classes
- Unit tests of the core `to_sqla` function
- Functional tests that execute the generated SQLAlchemy expressions against a sqlite database
- Functional tests of the CLI

These tests are parameterized (data driven) using data from `test/*.yaml`

SQL Support Checklist
---------------------

- [ ] Select

  - [x] Star: `SELECT * FROM foo`
  - [x] Multiple columns: `SELECT a, b, c FROM foo`
  - [x] Qualified column names: `SELECT foo.a, foo.b FROM foo`
  - [x] Column aliases: `SELECT foo.id AS foo_id, foo.name AS foo_name from FOO`
  - [ ] Joins

    - [x] Inner Join:

      - `SELECT * FROM foo JOIN bar`
      - `SELECT * FROM foo INNER JOIN bar`

    - [x] Cross Joins

      - `SELECT * FROM foo, bar`
      - `SELECT * FROM foo CROSS JOIN bar`

    - [ ] Left/Right Joins
    - [ ] Outer Joins

  - [x] On Clauses: `SELECT foo.a, bar.b FROM foo JOIN bar ON foo.id = bar.foo_id`
  - [x] Conjuctions (AND/OR): `SELECT foo.a, bar.b FROM foo join bar ON foo.id = bar.foo_id AND foo.val > 1`
  - [x] Select from subquery: `SELECT id FROM (SELECT * FROM foo)`
  - [x] Where: `SELECT id FROM foo WHERE id = 123`
  - [x] Between: `SELECT a FROM foo WHERE foo.val BETWEEN 1 AND 20`
  - [x] Select distinct: `SELECT DISTINCT a FROM foo`
  - [ ] Aggregate functions (SUM, AVG, COUNT, MIN, MAX): `SELECT COUNT(*) FROM foo`
  - [ ] Group by: `SELECT COUNT(*) FROM foo GROUP BY column`
  - [ ] Like
  - [ ] Limit/offset
  - [ ] Order by

- [ ] Insert
- [ ] Update
- [ ] Delete
