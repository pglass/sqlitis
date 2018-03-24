Overview
--------

This is a basic web UI for sqlitis. It uses flask to serve a React-based UI.

Use `yarn`_ to install dependencies,

.. code-block:: bash

    $ yarn install

Install the ``sqlitis`` web dependencies:

.. code-block:: bash

    $ pip install sqlitis[web]

Build the Javascript bundle:

.. code-block:: bash

    $ webpack --mode production

    $ webpack --mode development

Start the web server (requires ``sqlitis`` to be installed).

 .. code-block:: bash

    $ sqlitis --web

    ### dev mode
    $ sqlitis --web --debug


_yarn: https://yarnpkg.com/en/docs/install
