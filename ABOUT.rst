`BioBlend <https://bioblend.readthedocs.io/>`_ is a Python library for
interacting with `Galaxy`_ and `CloudMan`_  APIs.

BioBlend is supported and tested on:

- Python 3.5, 3.6, 3.7 and 3.8
- Galaxy release_17.09 and later.

BioBlend's goal is to make it easier to script and automate the running of
Galaxy analyses, administering of a Galaxy server, and cloud infrastructure
provisioning and scaling via CloudMan.
In practice, it makes it possible to do things like this:

- Interact with Galaxy via a straightforward API::

    from bioblend.galaxy import GalaxyInstance
    gi = GalaxyInstance('<Galaxy IP>', key='your API key')
    libs = gi.libraries.get_libraries()
    gi.workflows.show_workflow('workflow ID')
    gi.workflows.run_workflow('workflow ID', input_dataset_map)

- Interact with Galaxy via an object-oriented API::

    from bioblend.galaxy.objects import GalaxyInstance
    gi = GalaxyInstance("URL", "API_KEY")
    wf = gi.workflows.list()[0]
    hist = gi.histories.list()[0]
    inputs = hist.get_datasets()[:2]
    input_map = dict(zip(wf.input_labels, inputs))
    params = {"Paste1": {"delimiter": "U"}}
    wf.run(input_map, "wf_output", params=params)

- Create a CloudMan compute cluster, via an API and directly from your
  local machine::

    from bioblend.cloudman import CloudManConfig
    from bioblend.cloudman import CloudManInstance
    cfg = CloudManConfig('<your cloud access key>', '<your cloud secret key>', 'My CloudMan',  'ami-<ID>', 'm1.small', '<password>')
    cmi = CloudManInstance.launch_instance(cfg)
    cmi.get_status()

- Reconnect to an existing CloudMan instance and manipulate it::

    from bioblend.cloudman import CloudManInstance
    cmi = CloudManInstance("<instance IP>", "<password>")
    cmi.add_nodes(3)
    cluster_status = cmi.get_status()
    cmi.remove_nodes(2)

.. note::
    Although this library allows you to blend these two services into
    a cohesive unit, the library itself can be used with either
    service irrespective of the other. For example, you can use it to
    just manipulate CloudMan clusters or to script the interactions
    with an instance of Galaxy running on your laptop.

.. References/hyperlinks used above
.. _CloudMan: https://galaxyproject.org/cloudman/
.. _Galaxy: https://galaxyproject.org/
