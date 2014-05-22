`BioBlend <http://bioblend.readthedocs.org/>`_ is a Python (2.6 or 2.7)
library for interacting with `CloudMan`_ and `Galaxy`_'s API.

Conceptually, it makes it possible to script and automate the process of
cloud infrastructure provisioning and scaling via CloudMan, and running of analyses
via Galaxy. In reality, it makes it possible to do things like this:

- Create a CloudMan compute cluster, via an API and directly from your local machine::

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

.. note::
    Although this library allows you to blend these two services into a cohesive unit,
    the library itself can be used with either service irrespective of the other. For
    example, you can use it to just manipulate CloudMan clusters or to script the
    interactions with an instance of Galaxy running on your laptop.

.. References/hyperlinks used above
.. _CloudMan: http://usecloudman.org/
.. _Galaxy: http://usegalaxy.org/
.. _Git repository: https://github.com/afgane/bioblend
