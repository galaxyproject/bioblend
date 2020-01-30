===================
Usage documentation
===================

This page describes some sample use cases for CloudMan API and provides
examples for these API calls.
In addition to this page, there are functional examples of complete scripts in
``docs/examples`` directory of the BioBlend source code repository.

Setting up custom cloud properties
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
CloudMan supports Amazon, OpenStack, OpenNebula, and Eucalyptus based clouds and
BioBlend can be used to programatically manipulate CloudMan on any of those
clouds. Once launched, the API calls to CloudMan are the same irrespective of
the cloud. In order to launch an instance on a given cloud, cloud properties
need to be provided to ``CloudManLauncher``. If cloud properties are not specified,
``CloudManLauncher`` will default to Amazon cloud properties.

If we want to use a different cloud provider, we need to specify additional cloud
properties when creating an instance of the ``CloudManLauncher`` class. For
example, if we wanted to create a connection to `NeCTAR`_, Australia's national
research cloud, we would use the following properties::

    from bioblend.util import Bunch
    nectar = Bunch(
        name='NeCTAR',
        cloud_type='openstack',
        bucket_default='cloudman-os',
        region_name='NeCTAR',
        region_endpoint='nova.rc.nectar.org.au',
        ec2_port=8773,
        ec2_conn_path='/services/Cloud',
        cidr_range='115.146.92.0/22',
        is_secure=True,
        s3_host='swift.rc.nectar.org.au',
        s3_port=8888,
        s3_conn_path='/')

.. Note:: These properties are cloud-specific and need to be obtained from a
          given cloud provider.

Launching a new cluster instance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In order to launch a CloudMan cluster on a chosen cloud, we do the following
(continuing from the previous example)::

    from bioblend.cloudman import CloudManConfig
    from bioblend.cloudman import CloudManInstance
    cmc = CloudManConfig('<your AWS access key', 'your AWS secret key', 'Cluster name',
         'ami-<ID>', 'm1.medium', 'choose_a_password_here', nectar)
    cmi = CloudManInstance.launch_instance(cmc)

.. Note:: If you already have an existing instance of CloudMan, just create an
          instance of the ``CloudManInstance`` object directly by calling its
          constructor and connecting to it (the password you provide must match
          the password you provided as part of user data when launching this
          instance). For example::

            cmi = CloudManInstance('http://115.146.92.174', 'your_UD_password')

We now have a ``CloudManInstance`` object that allows us to manage created
CloudMan instance via the API. Once launched, it will take a few minutes for the
instance to boot and CloudMan start. To check on the status of the machine,
(repeatedly) run the following command::

    >>> cmi.get_machine_status()
    {'error': '',
     'instance_state': 'pending',
     'placement': '',
     'public_ip': ''}
    >>> cmi.get_machine_status()
    {'error': '',
     'instance_state': 'running',
     'placement': 'melbourne-qh2',
     'public_ip': '115.146.86.29'}

Once the instance is ready, although it may still take a few moments for CloudMan
to start, it is possible to start interacting with the application.

.. Note:: The ``CloudManInstance`` object (e.g., ``cmi``) is a local representation
          of the actual CloudMan instance. As a result, the local object can get
          out of sync with the remote instance. To update the state of the local
          object, call the ``update`` method on the ``cmi`` object::

              >>> cmi.update()


Manipulating an existing cluster
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Having a reference to a ``CloudManInstance`` object, we can manage it via the
available :ref:`cloudman-instance-api` API::

    >>> cmi.initialized
    False
    >>> cmi.initialize('SGE')
    >>> cmi.get_status()
    {'all_fs': [],
     'app_status': 'yellow',
     'autoscaling': {'as_max': 'N/A',
     'as_min': 'N/A',
     'use_autoscaling': False},
     'cluster_status': 'STARTING',
     'data_status': 'green',
     'disk_usage': {'pct': '0%', 'total': '0', 'used': '0'},
     'dns': '#',
     'instance_status': {'available': '0', 'idle': '0', 'requested': '0'},
     'snapshot': {'progress': 'None', 'status': 'None'}}
    >>> cmi.get_cluster_size()
    1
    >>> cmi.get_nodes()
    [{'id': 'i-00006016',
      'instance_type': 'm1.medium',
      'ld': '0.0 0.025 0.065',
      'public_ip': '115.146.86.29',
      'time_in_state': '2268'}]
    >>> cmi.add_nodes(2)
    {'all_fs': [],
     'app_status': 'green',
     'autoscaling': {'as_max': 'N/A',
      'as_min': 'N/A',
      'use_autoscaling': False},
     'cluster_status': 'READY',
     'data_status': 'green',
     'disk_usage': {'pct': '0%', 'total': '0', 'used': '0'},
     'dns': '#',
     'instance_status': {'available': '0', 'idle': '0', 'requested': '2'},
     'snapshot': {'progress': 'None', 'status': 'None'}}
    >>> cmi.get_cluster_size()
    3

.. _NeCTAR: http://www.nectar.org.au/research-cloud

