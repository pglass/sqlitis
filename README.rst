=========
 sqlitis
=========

A tool to convert raw sql to a sqlalchemy core expression.

.. code-block:: bash

    $ pip install sqlitis


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

