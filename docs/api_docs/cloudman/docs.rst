===================
Usage documentation
===================

This page describes some sample use cases for CloudMan API and provides
examples for these API calls.
In addition to this page, there are functional examples of complete scripts in
``docs/examples`` directory of the BioBlend source code repository.

Setting up a custom cloud connection
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
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
         'ami-<ID>', 'm1.medium', 'choose_a_password_here', nectar, 'SGE')
    cmi = CloudManInstance.launch_instance(cmc)

We now have a ``CloudManInstance`` object that allows us to manage created
CloudMan instance via the API.

.. Note:: The ``CloudManInstance`` object is a local representation of the actual
          CloudMan instance. As a result, the local object can get out of sync with
          the remote instance. To update the state of the local instance, call ``get_machine_status`` method::

            >>> cmi.get_machine_status()
            {'error': '',
             'instance_state': u'running',
             'placement': u'melbourne-qh2',
             'public_ip': u'115.146.86.29'}

Manipulating an instance
~~~~~~~~~~~~~~~~~~~~~~~~

Having a reference to a ``CloudManInstance`` object, we can manage it via the
available API methods::

    >>> cmi
    CloudMan instance at http://115.146.86.29/cloud
    >>> cmi.initialized
    True
    >>> cmi.get_cluster_size()
    1
    >>> cmi.get_nodes()Out[50]:
    [{u'id': u'i-00006016',
      u'instance_type': u'm1.medium',
      u'ld': u'0.0 0.025 0.065',
      u'public_ip': u'115.146.86.29',
      u'time_in_state': u'2268'}]
    >>> cmi.add_nodes(2)
    {u'all_fs': [],
     u'app_status': u'green',
     u'autoscaling': {u'as_max': u'N/A',
      u'as_min': u'N/A',
      u'use_autoscaling': False},
     u'cluster_status': u'READY',
     u'data_status': u'green',
     u'disk_usage': {u'pct': u'0%', u'total': u'0', u'used': u'0'},
     u'dns': u'#',
     u'instance_status': {u'available': u'0', u'idle': u'0', u'requested': u'2'},
     u'snapshot': {u'progress': u'None', u'status': u'None'}}
    >>> cmi.get_cluster_size()
    3

.. _NeCTAR: http://www.nectar.org.au/research-cloud
