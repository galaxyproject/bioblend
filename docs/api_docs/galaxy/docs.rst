===================
Usage documentation
===================

This page describes some sample use cases for the Galaxy API and provides
examples for these API calls.
In addition to this page, there are functional examples of complete scripts in
``docs/examples`` directory of the BioBlend source code repository.

Connect to a Galaxy server
~~~~~~~~~~~~~~~~~~~~~~~~~~

To connect to a running Galaxy server, you will need an account on that Galaxy instance and an API key for the account. Instructions on getting an API key can be found at http://wiki.galaxyproject.org/Learn/API .

To open a connection we use::

    from bioblend.galaxy import GalaxyInstance
    
    gi = GalaxyInstance(url='http://example.galaxy.url', key='your-API-key')

We now have a ``GalaxyInstance`` object which allows us to interact with the Galaxy server under our account, and access our data. If the account is a Galaxy admin account we also will be able to use this connection to carry out admin actions.

Histories and Datasets
~~~~~~~~~~~~~~~~~~~~~~

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


Data Libraries
~~~~~~~~~~~~~~

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

We can get files into Data Libraries in several ways: by uploading from our local machine, by retrieving from a URL, by passing the new file content directly into the method, or by importing a file from the filesystem on the Galaxy server.

For instance, to upload a file from our machine we might call:

    >>> gi.libraries.upload_file_from_local_path('8e6f930d00d123ea', '/local/path/to/mydata.fastq', file_type='fastqsanger')

Note that we have provided the id of the destination Data Library, and in this case we have specified the type that Galaxy should assign to the new dataset. The default value for ``file_type`` is 'auto', in which case Galaxy will attempt to guess the dataset type.

Workflows
~~~~~~~~~

Methods for accessing workflows are grouped under ``GalaxyInstance.workflows.*``. Currently, the Galaxy API allows us to run existing workflows or to import or export them as json.

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



Managing Users
~~~~~~~~~~~~~~

User management is only available to Galaxy administrators, that is, the API key used to connect to Galaxy must be that of an admin account.

To get a list of users, we can call:
    
    >>> gi.users.get_users()
    [{u'email': u'userA@unimelb.edu.au',
      u'id': u'975a9ce09b49502a',
      u'quota_percent': None,
      u'url': u'/api/users/975a9ce09b49502a'},
     {u'email': u'userB@student.unimelb.edu.au',
      u'id': u'0193a95acf427d2c',
      u'quota_percent': None,
      u'url': u'/api/users/0193a95acf427d2c'}]
