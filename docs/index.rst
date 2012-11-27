========
BioBlend
========

About
=====

.. include:: ../README.rst

Installation
============

Stable releases of BioBlend are best installed via ``pip`` or ``easy_install`` from
PyPI using something like::

    $ pip install bioblend

Alternatively, you may install the most current source code from our `Git repository`_,
or fork the project on Github. To install from source, do the following::

    # Clone the repository to a local directory
    $ git clone https://github.com/afgane/bioblend.git
    # Install the library
    $ cd bioblend
    $ python setup.py install

After installing the library, you will be able to simply import it into your
Python environment with ``import bioblend``. For details on the available functionality,
see the `API documentation`_.

Usage
=====

To get started using BioBlend, it's probably best to take a look at the example
scripts in ``docs/examples`` source directory and browse the `API documentation`_.
Beyond that, it's up to your creativity :).

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

CloudMan API
~~~~~~~~~~~~

API used to manipulate the instantiated infrastructure. For example, scale the
size of the compute cluster, get infrastructure status, get service status.

.. toctree::
    :maxdepth: 2
    :glob:

    api_docs/cloudman/*

Galaxy API
~~~~~~~~~~

API used to manipulate genomic analyses within Galaxy, including data management
and workflow execution.

.. toctree::
    :maxdepth: 2
    :glob:

    api_docs/galaxy/*


Testing
=======
The unit tests, in the ``tests`` folder, can be run using
`nose <https://github.com/nose-devs/nose>`_. From the project root::

    $ nosetests

Getting help
============

If you've run into issues, found a bug, or can't seem to find an answer to
your question regarding the use and functionality of BioBlend, please use
`Github Issues <https://github.com/afgane/bioblend/issues>`_ page to ask your
question

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

.. References/hyperlinks used above
.. _CloudMan: http://usecloudman.org/
.. _Galaxy: http://usegalaxy.org/
.. _Git repository: https://github.com/afgane/bioblend

