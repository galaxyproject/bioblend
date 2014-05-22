===================
Usage documentation
===================

This page describes some sample use cases for the Galaxy API and provides
examples for these API calls.
In addition to this page, there are functional examples of complete scripts in the 
``docs/examples`` directory of the BioBlend source code repository.

Connect to a Galaxy server
~~~~~~~~~~~~~~~~~~~~~~~~~~

To connect to a running Galaxy server, you will need an account on that Galaxy instance and an API key for the account. Instructions on getting an API key can be found at http://wiki.galaxyproject.org/Learn/API .

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
    [{u'id': u'f3c2b0f3ecac9f02',
      u'name': u'RNAseq_DGE_BASIC_Prep',
      u'url': u'/api/histories/f3c2b0f3ecac9f02'},
     {u'id': u'8a91dcf1866a80c2',
      u'name': u'June demo',
      u'url': u'/api/histories/8a91dcf1866a80c2'}]
    
This returns a list of dictionaries containing basic metadata, including the id and name of each History. In this case, we have two existing Histories in our account, 'RNAseq_DGE_BASIC_Prep' and 'June demo'. To get more detailed information about a History we can pass its id to the ``show_history`` method::

    >>> gi.histories.show_history('f3c2b0f3ecac9f02', contents=False)
    {u'annotation': u'',
     u'contents_url': u'/api/histories/f3c2b0f3ecac9f02/contents',
     u'id': u'f3c2b0f3ecac9f02',
     u'name': u'RNAseq_DGE_BASIC_Prep',
     u'nice_size': u'93.5 MB',
     u'state': u'ok',
     u'state_details': {u'discarded': 0,
          u'empty': 0,
          u'error': 0,
          u'failed_metadata': 0,
          u'new': 0,
          u'ok': 7,
          u'paused': 0,
          u'queued': 0,
          u'running': 0,
          u'setting_metadata': 0,
          u'upload': 0 },
     u'state_ids': {u'discarded': [],
          u'empty': [],
          u'error': [],
          u'failed_metadata': [],
          u'new': [],
          u'ok': [u'd6842fb08a76e351',
                  u'10a4b652da44e82a',
                  u'81c601a2549966a0',
                  u'a154f05e3bcee26b',
                  u'1352fe19ddce0400',
                  u'06d549c52d753e53',
                  u'9ec54455d6279cc7'],
          u'paused': [],
          u'queued': [],
          u'running': [],
          u'setting_metadata': [],
          u'upload': [] 
          } 
      }

.. _example-dataset:

This gives us a dictionary containing the History's metadata. With ``contents=False`` (the default), we only get a list of ids of the datasets contained within the History; with ``contents=True`` we would get metadata on each dataset. We can also directly access more detailed information on a particular dataset by passing its id to the ``show_dataset`` method::

    >>> gi.datasets.show_dataset('10a4b652da44e82a')
    {u'data_type': u'fastqsanger',
     u'deleted': False,
     u'file_size': 16527060,
     u'genome_build': u'dm3',
     u'id': 17499,
     u'metadata_data_lines': None,
     u'metadata_dbkey': u'dm3',
     u'metadata_sequences': None,
     u'misc_blurb': u'15.8 MB',
     u'misc_info': u'Noneuploaded fastqsanger file',
     u'model_class': u'HistoryDatasetAssociation',
     u'name': u'C1_R2_1.chr4.fq',
     u'purged': False,
     u'state': u'ok',
     u'visible': True}    

View Data Libraries
~~~~~~~~~~~~~~~~~~~

Methods for accessing Data Libraries are grouped under ``GalaxyInstance.libraries.*``. Most Data Library methods are available to all users, but as only administrators can create new Data Libraries within Galaxy, the ``create_folder`` and ``create_library`` methods can only be called using an API key belonging to an admin account.

We can view the Data Libraries available to our account using::

    >>> gi.libraries.get_libraries()
    [{u'id': u'8e6f930d00d123ea',
      u'name': u'RNA-seq workshop data',
      u'url': u'/api/libraries/8e6f930d00d123ea'},
     {u'id': u'f740ab636b360a70',
      u'name': u'1000 genomes',
      u'url': u'/api/libraries/f740ab636b360a70'}]

This gives a list of metadata dictionaries with basic information on each library. We can get more information on a particular Data Library by passing its id to the ``show_library`` method::

    >>> gi.libraries.show_library('8e6f930d00d123ea')
    {u'contents_url': u'/api/libraries/8e6f930d00d123ea/contents',
     u'description': u'RNA-Seq workshop data',
     u'name': u'RNA-Seq',
     u'synopsis': u'Data for the RNA-Seq tutorial'}

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
    [{u'id': u'e8b85ad72aefca86',
      u'name': u"TopHat + cufflinks part 1",
      u'url': u'/api/workflows/e8b85ad72aefca86'},
     {u'id': u'b0631c44aa74526d',
      u'name': u'CuffDiff',
      u'url': u'/api/workflows/b0631c44aa74526d'}]

This returns a list of metadata dictionaries. We can get the details of a particular Workflow, including its steps, by passing its id to the ``show_workflow`` method::

    >>> gi.workflows.show_workflow('e8b85ad72aefca86')
    {u'id': u'e8b85ad72aefca86',
     u'inputs': 
        {u'252': 
           {u'label': u'Input RNA-seq fastq', 
            u'value': u''
            }
         },
     u'name': u"TopHat + cufflinks part 1",
     u'steps': 
        {u'250': 
           {u'id': 250,
            u'input_steps': 
               {u'input1': 
                  {u'source_step': 252,
                   u'step_output': u'output'
                   }
               },
            u'tool_id': u'tophat',
            u'type': u'tool'
            },
         u'251': 
            {u'id': 251,
             u'input_steps': 
                {u'input': 
                   {u'source_step': 250,
                    u'step_output': u'accepted_hits'
                    }
                },
             u'tool_id': u'cufflinks',
             u'type': u'tool'
             },
         u'252': 
            {u'id': 252,
             u'input_steps': {},
             u'tool_id': None,
             u'type': u'data_input'
             }
         },
     u'url': u'/api/workflows/e8b85ad72aefca86'
     }

Export or import a Workflow
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Workflows can be exported from or imported into Galaxy as JSON. This makes it possible to archive Workflows, or to move them between Galaxy instances. 

To export a workflow, we can call::

    >>> workflow_string = gi.workflows.export_workflow_json('e8b85ad72aefca86')

This gives us a (rather long) string with a JSON-encoded representation of the Workflow. We can import this string as a new Workflow with::

    >>> gi.workflows.import_workflow_json(workflow_string)
    {u'id': u'c0bacafdfe211f9a',
     u'name': u'TopHat + cufflinks part 1 (imported from API)',
     u'url': u'/api/workflows/c0bacafdfe211f9a'}
     
This call returns a dictionary containing basic metadata on the new Workflow object. Since in this case we have imported the JSON string into the original Galaxy instance, we now have a duplicate of the original Workflow in our account:

    >>> gi.workflows.get_workflows()
    [{u'id': u'c0bacafdfe211f9a',
      u'name': u'TopHat + cufflinks part 1 (imported from API)',
      u'url': u'/api/workflows/c0bacafdfe211f9a'},
     {u'id': u'e8b85ad72aefca86',
      u'name': u"TopHat + cufflinks part 1",
      u'url': u'/api/workflows/e8b85ad72aefca86'},
     {u'id': u'b0631c44aa74526d',
      u'name': u'CuffDiff',
      u'url': u'/api/workflows/b0631c44aa74526d'}]

Instead of using JSON strings directly, Workflows can be exported to or imported from files on the local disk using the ``export_workflow_to_local_path`` and ``import_workflow_from_local_path`` methods. See the :ref:`API reference <workflows-api>` for details.

.. Note:: If we export a Workflow from one Galaxy instance and import it into another, Galaxy will only run it without modification if it has the same versions of the tool wrappers installed. This is to ensure reproducibility. Otherwise, we will need to manually update the Workflow to use the new tool versions.


Run a Workflow
~~~~~~~~~~~~~~

To run a Workflow, we need to tell Galaxy which datasets to use for which workflow inputs. We can use datasets from Histories or Data Libraries.

Examine the Workflow above. We can see that it takes only one input file. That is:

        >>> wf = gi.workflows.show_workflow('e8b85ad72aefca86')
        >>> wf['inputs']
        {u'252': 
            {u'label': 
                u'Input RNA-seq fastq', 
                u'value': u''
            }
        }
        
There is one input, labelled 'Input RNA-seq fastq'. This input is passed to the Tophat tool and should be a fastq file. We will use the dataset we examined above, under :ref:`view-histories-and-datasets`, which had name 'C1_R2_1.chr4.fq' and id '10a4b652da44e82a'.

To specify the inputs, we build a data map and pass this to the ``run_workflow`` method. This data map is a nested dictionary object which maps inputs to datasets. We call::

    >>> datamap = dict()
    >>> datamap['252'] = { 'src':'hda', 'id':'10a4b652da44e82a' }
    >>> gi.workflows.run_workflow('e8b85ad72aefca86', datamap, history_name='New output history')
    {u'history': u'0a7b7992a7cabaec',
     u'outputs': [u'33be8ad9917d9207',
                  u'fbee1c2dc793c114',
                  u'85866441984f9e28',
                  u'1c51aa78d3742386',
                  u'a68e8770e52d03b4',
                  u'c54baf809e3036ac',
                  u'ba0db8ce6cd1fe8f',
                  u'c019e4cf08b2ac94'
                  ]
    }

In this case the only input id is '252' and the corresponding dataset id is '10a4b652da44e82a'. We have specified the dataset source to be 'hda' (HistoryDatasetAssociation) since the dataset is stored in a History. See the :ref:`API reference <workflows-api>` for allowed dataset specifications. We have also requested that a new History be created and used to store the results of the run, by setting ``history_name='New output history'``.

The ``run_workflow`` call submits all the jobs which need to be run to the Galaxy workflow engine, with the appropriate dependencies so that they will run in order. The call returns immediately, so we can continue to submit new jobs while waiting for this workflow to execute. ``run_workflow`` returns the id of the output History and of the datasets that will be created as a result of this run. Note that these dataset ids are valid immediately, so we can specify these datasets as inputs to new jobs even before the files have been created, and the new jobs will be added to the queue with the appropriate dependencies.

If we view the output History immediately after calling ``run_workflow``, we will see something like::

    >>> gi.histories.show_history('0a7b7992a7cabaec')
    {u'annotation': u'',
     u'contents_url': u'/api/histories/0a7b7992a7cabaec/contents',
     u'id': u'0a7b7992a7cabaec',
     u'name': u'New output history',
     u'nice_size': u'0 bytes',
     u'state': u'queued',
     u'state_details': {u'discarded': 0,
         u'empty': 0,
         u'error': 0,
         u'failed_metadata': 0,
         u'new': 0,
         u'ok': 0,
         u'paused': 0,
         u'queued': 8,
         u'running': 0,
         u'setting_metadata': 0,
         u'upload': 0},
     u'state_ids': {u'discarded': [],
         u'empty': [],
         u'error': [],
         u'failed_metadata': [],
         u'new': [],
         u'ok': [],
         u'paused': [],
         u'queued': [u'33be8ad9917d9207',
                     u'fbee1c2dc793c114',
                     u'85866441984f9e28',
                     u'1c51aa78d3742386',
                     u'a68e8770e52d03b4',
                     u'c54baf809e3036ac',
                     u'ba0db8ce6cd1fe8f',
                     u'c019e4cf08b2ac94'],
         u'running': [],
         u'setting_metadata': [],
         u'upload': []
        }
    }

In this case, because the submitted jobs have not had time to run, the output History contains 8 datasets in the 'queued' state and has a total size of 0 bytes. If we make this call again later we should instead see completed output files.

View Users
~~~~~~~~~~

Methods for managing users are grouped under ``GalaxyInstance.users.*``. User management is only available to Galaxy administrators, that is, the API key used to connect to Galaxy must be that of an admin account.

To get a list of users, call:
    
    >>> gi.users.get_users()
    [{u'email': u'userA@unimelb.edu.au',
      u'id': u'975a9ce09b49502a',
      u'quota_percent': None,
      u'url': u'/api/users/975a9ce09b49502a'},
     {u'email': u'userB@student.unimelb.edu.au',
      u'id': u'0193a95acf427d2c',
      u'quota_percent': None,
      u'url': u'/api/users/0193a95acf427d2c'}]
