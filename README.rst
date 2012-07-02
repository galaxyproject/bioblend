`Blend <http://blend.readthedocs.org/en/latest/>`_ is a Python (2.6 or higher)
library for interacting with `BioCloudCentral.org`_, `CloudMan`_, and `Galaxy`_'s
API. Conceptually, it makes it possible to script and automate the process of
cloud infrastrucutre provisioning and scaling, as well as running of analyses
within Galaxy. In reality, it makes it possible to do things like this:

- Create a CloudMan compute cluster, direclty from your local machine::

    from blend.bcc import BCC
    user_data = {}
    user_data['cluster_name'] = 'Started from blend'
    user_data['access_key'] = 'Your cloud access key'
    user_data['secret_key'] = 'Your cloud secret key'
    c = BCC.launch(ud=user_data, image_id='ami-e23943jd')

- Manipulate your CloudMan instance and react to the current needs::

    from blend.cloudman import CloudMan
    cm = CloudMan("instance IP", "password")
    cm.initialize(type="Galaxy")
    cm.add_nodes(3)
    cluster_status = cm.get_status()
    cm.remove_nodes(2)

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

