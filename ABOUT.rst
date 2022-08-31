`BioBlend <https://bioblend.readthedocs.io/>`_ is a Python library for
interacting with the `Galaxy`_ API.

BioBlend is supported and tested on:

- Python 3.7, 3.8, 3.9 and 3.10
- Galaxy release 17.09 and later.

BioBlend's goal is to make it easier to script and automate the running of
Galaxy analyses and administering of a Galaxy server.
In practice, it makes it possible to do things like this:

- Interact with Galaxy via a straightforward API::

    from bioblend.galaxy import GalaxyInstance
    gi = GalaxyInstance('<Galaxy IP>', key='your API key')
    libs = gi.libraries.get_libraries()
    gi.workflows.show_workflow('workflow ID')
    wf_invocation = gi.workflows.invoke_workflow('workflow ID', inputs)

- Interact with Galaxy via an object-oriented API::

    from bioblend.galaxy.objects import GalaxyInstance
    gi = GalaxyInstance("URL", "API_KEY")
    wf = gi.workflows.list()[0]
    hist = gi.histories.list()[0]
    inputs = hist.get_datasets()[:2]
    input_map = dict(zip(wf.input_labels, inputs))
    params = {"Paste1": {"delimiter": "U"}}
    wf_invocation = wf.invoke(input_map, params=params)

About the library name
~~~~~~~~~~~~~~~~~~~~~~

The library was originally called just ``Blend`` but we
`renamed it <https://github.com/galaxyproject/bioblend/commit/d01bd083c74ad6d890272f5a71bfa214d4d5279c>`_
to reflect more of its domain and a make it bit more unique so it can be easier to find.
The name was intended to be short and easily pronounceable. In its original
implementation, the goal was to provide a lot more support for `CloudMan`_
and other integration capabilities, allowing them to be *blended* together
via code. ``BioBlend`` fitted the bill.

.. References/hyperlinks used above
.. _CloudMan: https://galaxyproject.org/cloudman/
.. _Galaxy: https://galaxyproject.org/
