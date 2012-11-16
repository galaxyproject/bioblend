`Blend <http://blend.readthedocs.org/en/latest/>`_ is a Python (2.6 or higher)
library for interacting with `CloudMan`_, and `Galaxy`_'s API.
Conceptually, it makes it possible to script and automate the process of
cloud infrastrucutre provisioning and scaling, as well as running of analyses
within Galaxy. In reality, it makes it possible to do things like this:

- Create a CloudMan compute cluster, via an API and directly from your local machine::

    from blend.cloudman import CloudManConfig
	from blend.cloudman import CloudManInstance

    cfg = CloudManConfig('<your cloud access key>', '<your cloud secret key>', 'Blend CloudMan',  'ami-<ID>', 'm1.small', '<password>')
	cmi = CloudManInstance.launch_instance(cfg)    
    cmi.get_status()

- Reconnect to an existing CloudMan instance and manipulate it:

    from blend.cloudman import CloudManInstance
    cmi = CloudManInstance("<instance IP>", "<password>")
    cmi.add_nodes(3)
    cluster_status = cmi.get_status()
    cmi.remove_nodes(2)

- Interact with Galaxy via a straighforward API::

    from blend.galaxy import GalaxyInstance
    gi = GalaxyInstance('<Galaxy IP>', key='your API key')
    libs = gi.libraries.get_libraries()
    gi.workflows.show_workflow('workflow ID')
    gi.workflows.run_workflow('workflow ID', input_dataset_map)

.. note::
    Although this library allows you to blend these three services into a cohesive unit,
    the library itself can be used with any single service irrespective of the rest. For
    example, you can use it to just manipulate CloudMan clusters or to script the
    interactions with an instance of Galaxy running on your laptop.

