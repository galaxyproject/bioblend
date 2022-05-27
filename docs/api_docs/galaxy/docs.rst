===================
Usage documentation
===================

This page describes some sample use cases for the Galaxy API and provides
examples for these API calls.
In addition to this page, there are functional examples of complete scripts in the
``docs/examples`` directory of the BioBlend source code repository.

Connect to a Galaxy server
~~~~~~~~~~~~~~~~~~~~~~~~~~

To connect to a running Galaxy server, you will need an account on that Galaxy instance and an API key for the account. Instructions on getting an API key can be found at https://galaxyproject.org/develop/api/ .

To open a connection call::

    from bioblend.galaxy import GalaxyInstance

    gi = GalaxyInstance(url='http://example.galaxy.url', key='your-API-key')

We now have a ``GalaxyInstance`` object which allows us to interact with the Galaxy server under our account, and access our data. If the account is a Galaxy admin account we also will be able to use this connection to carry out admin actions.

.. _view-histories-and-datasets:

View Histories and Datasets
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Methods for accessing histories and datasets are grouped under ``GalaxyInstance.histories.*`` and ``GalaxyInstance.datasets.*`` respectively.

To get information on the Histories currently in your account, call::

    >>> gi.histories.get_histories()
    [{'id': 'f3c2b0f3ecac9f02',
      'name': 'RNAseq_DGE_BASIC_Prep',
      'url': '/api/histories/f3c2b0f3ecac9f02'},
     {'id': '8a91dcf1866a80c2',
      'name': 'June demo',
      'url': '/api/histories/8a91dcf1866a80c2'}]

This returns a list of dictionaries containing basic metadata, including the id and name of each History. In this case, we have two existing Histories in our account, 'RNAseq_DGE_BASIC_Prep' and 'June demo'. To get more detailed information about a History we can pass its id to the ``show_history`` method::

    >>> gi.histories.show_history('f3c2b0f3ecac9f02', contents=False)
    {'annotation': '',
     'contents_url': '/api/histories/f3c2b0f3ecac9f02/contents',
     'id': 'f3c2b0f3ecac9f02',
     'name': 'RNAseq_DGE_BASIC_Prep',
     'nice_size': '93.5 MB',
     'state': 'ok',
     'state_details': {'discarded': 0,
                       'empty': 0,
                       'error': 0,
                       'failed_metadata': 0,
                       'new': 0,
                       'ok': 7,
                       'paused': 0,
                       'queued': 0,
                       'running': 0,
                       'setting_metadata': 0,
                       'upload': 0},
     'state_ids': {'discarded': [],
                   'empty': [],
                   'error': [],
                   'failed_metadata': [],
                   'new': [],
                   'ok': ['d6842fb08a76e351',
                          '10a4b652da44e82a',
                          '81c601a2549966a0',
                          'a154f05e3bcee26b',
                          '1352fe19ddce0400',
                          '06d549c52d753e53',
                          '9ec54455d6279cc7'],
                   'paused': [],
                   'queued': [],
                   'running': [],
                   'setting_metadata': [],
                   'upload': []}}

.. _example-dataset:

This gives us a dictionary containing the History's metadata. With ``contents=False`` (the default), we only get a list of ids of the datasets contained within the History; with ``contents=True`` we would get metadata on each dataset. We can also directly access more detailed information on a particular dataset by passing its id to the ``show_dataset`` method::

    >>> gi.datasets.show_dataset('10a4b652da44e82a')
    {'data_type': 'fastqsanger',
     'deleted': False,
     'file_size': 16527060,
     'genome_build': 'dm3',
     'id': 17499,
     'metadata_data_lines': None,
     'metadata_dbkey': 'dm3',
     'metadata_sequences': None,
     'misc_blurb': '15.8 MB',
     'misc_info': 'Noneuploaded fastqsanger file',
     'model_class': 'HistoryDatasetAssociation',
     'name': 'C1_R2_1.chr4.fq',
     'purged': False,
     'state': 'ok',
     'visible': True}

Uploading Datasets to a History
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To upload a local file to a Galaxy server, you can run the ``upload_file`` method, supplying the path to a local file::

    >>> gi.tools.upload_file('test.txt', 'f3c2b0f3ecac9f02')
    {'implicit_collections': [],
     'jobs': [{'create_time': '2015-07-28T17:52:39.756488',
               'exit_code': None,
               'id': '9752b387803d3e1e',
               'model_class': 'Job',
               'state': 'new',
               'tool_id': 'upload1',
               'update_time': '2015-07-28T17:52:39.987509'}],
     'output_collections': [],
     'outputs': [{'create_time': '2015-07-28T17:52:39.331176',
                  'data_type': 'galaxy.datatypes.data.Text',
                  'deleted': False,
                  'file_ext': 'auto',
                  'file_size': 0,
                  'genome_build': '?',
                  'hda_ldda': 'hda',
                  'hid': 16,
                  'history_content_type': 'dataset',
                  'history_id': 'f3c2b0f3ecac9f02',
                  'id': '59c76a119581e190',
                  'metadata_data_lines': None,
                  'metadata_dbkey': '?',
                  'misc_blurb': None,
                  'misc_info': None,
                  'model_class': 'HistoryDatasetAssociation',
                  'name': 'test.txt',
                  'output_name': 'output0',
                  'peek': '<table cellspacing="0" cellpadding="3"></table>',
                  'purged': False,
                  'state': 'queued',
                  'tags': [],
                  'update_time': '2015-07-28T17:52:39.611887',
                  'uuid': 'ff0ee99b-7542-4125-802d-7a193f388e7e',
                  'visible': True}]}

If files are greater than 2GB in size, they will need to be uploaded via FTP. Importing files from the user's FTP folder can be done via running the upload tool again::

    >>> gi.tools.upload_from_ftp('test.txt', 'f3c2b0f3ecac9f02')
    {'implicit_collections': [],
     'jobs': [{'create_time': '2015-07-28T17:57:43.704394',
               'exit_code': None,
               'id': '82b264d8c3d11790',
               'model_class': 'Job',
               'state': 'new',
               'tool_id': 'upload1',
               'update_time': '2015-07-28T17:57:43.910958'}],
     'output_collections': [],
     'outputs': [{'create_time': '2015-07-28T17:57:43.209041',
                  'data_type': 'galaxy.datatypes.data.Text',
                  'deleted': False,
                  'file_ext': 'auto',
                  'file_size': 0,
                  'genome_build': '?',
                  'hda_ldda': 'hda',
                  'hid': 17,
                  'history_content_type': 'dataset',
                  'history_id': 'f3c2b0f3ecac9f02',
                  'id': 'a676e8f07209a3be',
                  'metadata_data_lines': None,
                  'metadata_dbkey': '?',
                  'misc_blurb': None,
                  'misc_info': None,
                  'model_class': 'HistoryDatasetAssociation',
                  'name': 'test.txt',
                  'output_name': 'output0',
                  'peek': '<table cellspacing="0" cellpadding="3"></table>',
                  'purged': False,
                  'state': 'queued',
                  'tags': [],
                  'update_time': '2015-07-28T17:57:43.544407',
                  'uuid': '2cbe8f0a-4019-47c4-87e2-005ce35b8449',
                  'visible': True}]}


View Data Libraries
~~~~~~~~~~~~~~~~~~~

Methods for accessing Data Libraries are grouped under ``GalaxyInstance.libraries.*``. Most Data Library methods are available to all users, but as only administrators can create new Data Libraries within Galaxy, the ``create_folder`` and ``create_library`` methods can only be called using an API key belonging to an admin account.

We can view the Data Libraries available to our account using::

    >>> gi.libraries.get_libraries()
    [{'id': '8e6f930d00d123ea',
      'name': 'RNA-seq workshop data',
      'url': '/api/libraries/8e6f930d00d123ea'},
     {'id': 'f740ab636b360a70',
      'name': '1000 genomes',
      'url': '/api/libraries/f740ab636b360a70'}]

This gives a list of metadata dictionaries with basic information on each library. We can get more information on a particular Data Library by passing its id to the ``show_library`` method::

    >>> gi.libraries.show_library('8e6f930d00d123ea')
    {'contents_url': '/api/libraries/8e6f930d00d123ea/contents',
     'description': 'RNA-Seq workshop data',
     'name': 'RNA-Seq',
     'synopsis': 'Data for the RNA-Seq tutorial'}

Upload files to a Data Library
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We can get files into Data Libraries in several ways: by uploading from our local machine, by retrieving from a URL, by passing the new file content directly into the method, or by importing a file from the filesystem on the Galaxy server.

For instance, to upload a file from our machine we might call:

    >>> gi.libraries.upload_file_from_local_path('8e6f930d00d123ea', '/local/path/to/mydata.fastq', file_type='fastqsanger')

Note that we have provided the id of the destination Data Library, and in this case we have specified the type that Galaxy should assign to the new dataset. The default value for ``file_type`` is 'auto', in which case Galaxy will attempt to guess the dataset type.

View Workflows
~~~~~~~~~~~~~~

Methods for accessing workflows are grouped under ``GalaxyInstance.workflows.*``.

To get information on the Workflows currently in your account, use::

    >>> gi.workflows.get_workflows()
    [{'id': 'e8b85ad72aefca86',
      'name': 'TopHat + cufflinks part 1',
      'url': '/api/workflows/e8b85ad72aefca86'},
     {'id': 'b0631c44aa74526d',
      'name': 'CuffDiff',
      'url': '/api/workflows/b0631c44aa74526d'}]

This returns a list of metadata dictionaries. We can get the details of a particular Workflow, including its steps, by passing its id to the ``show_workflow`` method::

    >>> gi.workflows.show_workflow('e8b85ad72aefca86')
    {'id': 'e8b85ad72aefca86',
     'inputs': {'252': {'label': 'Input RNA-seq fastq', 'value': ''}},
     'name': 'TopHat + cufflinks part 1',
     'steps': {'250': {'id': 250,
                       'input_steps': {'input1': {'source_step': 252,
                                                  'step_output': 'output'}},
                       'tool_id': 'tophat',
                       'type': 'tool'},
               '251': {'id': 251,
                       'input_steps': {'input': {'source_step': 250,
                                                 'step_output': 'accepted_hits'}},
                       'tool_id': 'cufflinks',
                       'type': 'tool'},
               '252': {'id': 252,
                       'input_steps': {},
                       'tool_id': None,
                       'type': 'data_input'}},
     'url': '/api/workflows/e8b85ad72aefca86'}

Export or import a workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Workflows can be exported from or imported into Galaxy. This makes it possible to archive workflows, or to move them between Galaxy instances.

To export a workflow, we can call::

    >>> workflow_dict = gi.workflows.export_workflow_dict('e8b85ad72aefca86')

This gives us a complex dictionary representing the workflow. We can import this dictionary as a new workflow with::

    >>> gi.workflows.import_workflow_dict(workflow_dict)
    {'id': 'c0bacafdfe211f9a',
     'name': 'TopHat + cufflinks part 1 (imported from API)',
     'url': '/api/workflows/c0bacafdfe211f9a'}

This call returns a dictionary containing basic metadata on the new workflow. Since in this case we have imported the dictionary into the original Galaxy instance, we now have a duplicate of the original workflow in our account:

    >>> gi.workflows.get_workflows()
    [{'id': 'c0bacafdfe211f9a',
      'name': 'TopHat + cufflinks part 1 (imported from API)',
      'url': '/api/workflows/c0bacafdfe211f9a'},
     {'id': 'e8b85ad72aefca86',
      'name': 'TopHat + cufflinks part 1',
      'url': '/api/workflows/e8b85ad72aefca86'},
     {'id': 'b0631c44aa74526d',
      'name': 'CuffDiff',
      'url': '/api/workflows/b0631c44aa74526d'}]

Instead of using dictionaries directly, workflows can be exported to or imported from files on the local disk using the ``export_workflow_to_local_path`` and ``import_workflow_from_local_path`` methods. See the :ref:`API reference <workflows-api>` for details.

.. Note:: If we export a workflow from one Galaxy instance and import it into another, Galaxy will only run it without modification if it has the same versions of the tool wrappers installed. This is to ensure reproducibility. Otherwise, we will need to manually update the workflow to use the new tool versions.


Invoke a workflow
~~~~~~~~~~~~~~~~~

To invoke a workflow, we need to tell Galaxy which datasets to use for which workflow inputs. We can use datasets from histories or data libraries.

Examine the workflow above. We can see that it takes only one input file. That is:

    >>> wf = gi.workflows.show_workflow('e8b85ad72aefca86')
    >>> wf['inputs']
    {'252': {'label': 'Input RNA-seq fastq', 'value': ''}}

There is one input, labelled 'Input RNA-seq fastq'. This input is passed to the Tophat tool and should be a fastq file. We will use the dataset we examined above, under :ref:`view-histories-and-datasets`, which had name 'C1_R2_1.chr4.fq' and id '10a4b652da44e82a'.

To specify the inputs, we build a data map and pass this to the ``invoke_workflow`` method. This data map is a nested dictionary object which maps inputs to datasets. We call::

    >>> datamap = {'252': {'src':'hda', 'id':'10a4b652da44e82a'}}
    >>> gi.workflows.invoke_workflow('e8b85ad72aefca86', inputs=datamap, history_name='New output history')
    {'history': '0a7b7992a7cabaec',
     'outputs': ['33be8ad9917d9207',
                 'fbee1c2dc793c114',
                 '85866441984f9e28',
                 '1c51aa78d3742386',
                 'a68e8770e52d03b4',
                 'c54baf809e3036ac',
                 'ba0db8ce6cd1fe8f',
                 'c019e4cf08b2ac94']}

In this case the only input id is '252' and the corresponding dataset id is '10a4b652da44e82a'. We have specified the dataset source to be 'hda' (HistoryDatasetAssociation) since the dataset is stored in a History. See the :ref:`API reference <workflows-api>` for allowed dataset specifications. We have also requested that a new History be created and used to store the results of the run, by setting ``history_name='New output history'``.

The ``invoke_workflow`` call submits all the jobs which need to be run to the Galaxy workflow engine, with the appropriate dependencies so that they will run in order. The call returns immediately, so we can continue to submit new jobs while waiting for this workflow to execute. ``invoke_workflow`` returns the a dictionary describing the workflow invocation.

If we view the output History immediately after calling ``invoke_workflow``, we will see something like::

    >>> gi.histories.show_history('0a7b7992a7cabaec')
    {'annotation': '',
     'contents_url': '/api/histories/0a7b7992a7cabaec/contents',
     'id': '0a7b7992a7cabaec',
     'name': 'New output history',
     'nice_size': '0 bytes',
     'state': 'queued',
     'state_details': {'discarded': 0,
                       'empty': 0,
                       'error': 0,
                       'failed_metadata': 0,
                       'new': 0,
                       'ok': 0,
                       'paused': 0,
                       'queued': 8,
                       'running': 0,
                       'setting_metadata': 0,
                       'upload': 0},
     'state_ids': {'discarded': [],
                   'empty': [],
                   'error': [],
                   'failed_metadata': [],
                   'new': [],
                   'ok': [],
                   'paused': [],
                   'queued': ['33be8ad9917d9207',
                              'fbee1c2dc793c114',
                              '85866441984f9e28',
                              '1c51aa78d3742386',
                              'a68e8770e52d03b4',
                              'c54baf809e3036ac',
                              'ba0db8ce6cd1fe8f',
                              'c019e4cf08b2ac94'],
                   'running': [],
                   'setting_metadata': [],
                   'upload': []}}

In this case, because the submitted jobs have not had time to run, the output History contains 8 datasets in the 'queued' state and has a total size of 0 bytes. If we make this call again later we should instead see completed output files.

View Users
~~~~~~~~~~

Methods for managing users are grouped under ``GalaxyInstance.users.*``. User management is only available to Galaxy administrators, that is, the API key used to connect to Galaxy must be that of an admin account.

To get a list of users, call:

    >>> gi.users.get_users()
    [{'email': 'userA@example.org',
      'id': '975a9ce09b49502a',
      'quota_percent': None,
      'url': '/api/users/975a9ce09b49502a'},
     {'email': 'userB@example.org',
      'id': '0193a95acf427d2c',
      'quota_percent': None,
      'url': '/api/users/0193a95acf427d2c'}]

Using BioBlend for raw API calls
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

BioBlend can be used to make HTTP requests to the Galaxy API in a more convenient way than using e.g. the ``requests`` Python library. There are 5 available methods corresponding to the most common HTTP methods: ``make_get_request``, ``make_post_request``, ``make_put_request``, ``make_delete_request`` and ``make_patch_request``.
One advantage of using these methods is that the API keys stored in the ``GalaxyInstance`` object is automatically added to the request.

To make a GET request to the Galaxy API with BioBlend, call:

    >>> gi.make_get_request(gi.base_url + "/api/version").json()
    {'version_major': '19.05',
     'extra': {}}

To make a POST request to the Galaxy API with BioBlend, call:

    >>> gi.make_post_request(gi.base_url + "/api/histories", payload={"name": "test history"})
    {'importable': False,
     'create_time': '2019-07-05T20:10:04.823716',
     'contents_url': '/api/histories/a77b3f95070d689a/contents',
     'id': 'a77b3f95070d689a',
     'size': 0, 'user_id': '5b732999121d4593',
     'username_and_slug': None,
     'annotation': None,
     'state_details': {'discarded': 0,
                       'ok': 0,
                       'failed_metadata': 0,
                       'upload': 0,
                       'paused': 0,
                       'running': 0,
                       'setting_metadata': 0,
                       'error': 0,
                       'new': 0,
                       'queued': 0,
                       'empty': 0},
     'state': 'new',
     'empty': True,
     'update_time': '2019-07-05T20:10:04.823742',
     'tags': [],
     'deleted': False,
     'genome_build': None,
     'slug': None,
     'name': 'test history',
     'url': '/api/histories/a77b3f95070d689a',
     'state_ids': {'discarded': [],
                   'ok': [],
                   'failed_metadata': [],
                   'upload': [],
                   'paused': [],
                   'running': [],
                   'setting_metadata': [],
                   'error': [],
                   'new': [],
                   'queued': [],
                   'empty': []},
     'published': False,
     'model_class': 'History',
     'purged': False}
