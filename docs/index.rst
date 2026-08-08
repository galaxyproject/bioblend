========
BioBlend
========

About
=====

.. include:: ../ABOUT.rst

Installation
============

Stable releases of BioBlend are best installed via ``pip`` from PyPI::

    $ python3 -m pip install bioblend

Alternatively, the most current source code from our `Git repository`_ can be
installed with::

    $ python3 -m pip install git+https://github.com/galaxyproject/bioblend

After installing the library, you will be able to simply import it into your
Python environment with ``import bioblend``. For details on the available functionality,
see the `API documentation`_.

If you also want to run tests locally, some extra libraries are required. To
install them, run::

    $ python3 -m pip install bioblend[testing]

Usage
=====

To get started using BioBlend, install the library as described above. Once the
library becomes available on the given system, it can be developed against.
The developed scripts do not need to reside in any particular location on the system.

It is probably best to take a look at the example scripts in ``docs/examples`` source
directory and browse the `API documentation`_. Beyond that, it's up to your creativity :).

Rate limiting
=============

Public Galaxy servers usually limit how many API requests a user may make in a
given period of time, and reject the requests made over that limit with HTTP
status 429 (Too Many Requests).

BioBlend retries such requests automatically, so scripts do not need to handle
them. When the server indicates through the ``Retry-After`` header how long to
wait, that delay is honoured. Otherwise BioBlend waits for a progressively
longer time between attempts. Every method is retried, including ``POST`` ones:
a 429 response means that the request was rejected before being processed, so
replaying it cannot duplicate anything on the server.

Retrying is bounded, so that a rate-limited call fails in a predictable amount
of time instead of blocking for as long as the server asks for. Once the total
time spent waiting reaches ``max_total_retry_delay`` (60 seconds by default), a
``bioblend.ConnectionError`` with a ``status_code`` of 429 is raised, just as if
no retrying had taken place. The bounds can be changed on the Galaxy (or
ToolShed) instance object::

    from bioblend.galaxy import GalaxyInstance

    gi = GalaxyInstance(url="https://usegalaxy.org", key="your_api_key")
    # Give up after a total of 5 minutes of waiting.
    gi.max_total_retry_delay = 300.0
    # Never wait more than 1 minute before a single retry.
    gi.max_retry_after = 60.0

Setting ``max_total_retry_delay`` to 0 disables retrying altogether.

Two kinds of requests are deliberately not retried: uploads sending a file as
multipart form data, because their body is a stream which cannot be replayed,
and requests which fail with a connection or read error, since those may have
reached the server.

Reusing connections
===================

By default, each request opens a new connection. Scripts making many requests
can reuse a single session instead, which avoids re-establishing a connection
every time. In the following example, one connection is used for the initial
request and for the one made for each history returned by it::

    with GalaxyInstance(url="https://usegalaxy.org", key="your_api_key") as gi:
        for history in gi.histories.get_histories():
            datasets = gi.histories.show_history(history["id"], contents=True)
            print(history["name"], len(datasets))

Equivalently, ``gi.use_session = True`` enables it and ``gi.close()`` releases
the connections. An instance with a session enabled should not be shared between
threads.

Development
===========

Anyone interested in contributing or tweaking the library is more then welcome
to do so. To start, simply fork the `Git repository`_ on Github and start playing with
it. Then, issue pull requests.

API Documentation
=================

BioBlend's API focuses around and matches the services it wraps. Thus, there are
two top-level sets of APIs, each corresponding to a separate service and a
corresponding step in the automation process. *Note* that each of the service APIs
can be used completely independently of one another.

Effort has been made to keep the structure and naming of those API's consistent
across the library but because they do bridge different services, some discrepancies
may exist. Feel free to point those out and/or provide fixes.

For Galaxy, an alternative :ref:`object-oriented API <objects-api>` is
also available.  This API provides an explicit modeling of server-side
Galaxy instances and their relationships, providing higher-level
methods to perform operations such as retrieving all datasets for a
given history, etc.  Note that, at the moment, the oo API is still
incomplete, providing access to a more restricted set of Galaxy
modules with respect to the standard one.

Galaxy API
~~~~~~~~~~

API used to manipulate genomic analyses within Galaxy, including data management
and workflow execution.

.. toctree::
    :maxdepth: 3
    :glob:

    api_docs/galaxy/*

Toolshed API
~~~~~~~~~~~~

API used to interact with the Galaxy Toolshed, including repository management.

.. toctree::
    :maxdepth: 3
    :glob:

    api_docs/toolshed/*

Configuration
=============
BioBlend allows library-wide configuration to be set in external files.
These configuration files can be used to specify access keys, for example.

.. toctree::
    :maxdepth: 1
    :glob:

    api_docs/lib_config

Testing
=======
If you would like to do more than just a mock test, you need to point
BioBlend to an instance of Galaxy. Do so by exporting the following
two variables::

    $ export BIOBLEND_GALAXY_URL=http://127.0.0.1:8080
    $ export BIOBLEND_GALAXY_API_KEY=<API key>

The unit tests, stored in the ``tests`` folder, can be run using
`pytest <https://docs.pytest.org/>`_. From the project root::

    $ pytest

Getting help
============

If you have run into issues, found a bug, or can't seem to find an answer to
your question regarding the use and functionality of BioBlend, please use the
`Github Issues <https://github.com/galaxyproject/bioblend/issues>`_ page to ask your
question.

Related documentation
=====================

Links to other documentation and libraries relevant to this library:

    * `Galaxy API documentation <https://galaxyproject.org/develop/api/>`_
    * `Blend4j <https://github.com/jmchilton/blend4j>`_: Galaxy API wrapper for Java
    * `clj-blend <https://github.com/chapmanb/clj-blend>`_: Galaxy API wrapper for Clojure

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. References/hyperlinks used above
.. _Git repository: https://github.com/galaxyproject/bioblend
.. _PyPi: https://pypi.org/project/bioblend/
