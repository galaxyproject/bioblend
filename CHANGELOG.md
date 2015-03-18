### BioBlend v0.5.3 - March 18, 2014

* Project source moved to new URL - https://github.com/galaxyproject/bioblend

* Huge improvements to automated testing, tests now run against Galaxy
  release_14.02 and all later versions to ensure backward compatibility
  (see `.travis.yml` for details).

* Many documentation improvements (thanks to Eric Rasche).

* Add Galaxy clients for the tool data tables, the roles, and library
  folders (thanks to Anthony Bretaudeau).

* Add method to get the standard error and standard output for the
  job corresponding to a Galaxy dataset (thanks to Anthony Bretaudeau).

* Add ``get_state()`` method to ``JobsClient``.

* Add ``copy_from_dataset()`` method to ``LibraryClient``.

* Add ``create_repository()`` method to ``ToolShedClient`` (thanks to Eric
  Rasche).

* Fix ``DatasetClient.download_dataset()`` for certain proxied Galaxy
  deployments.

* Make ``LibraryClient._get_root_folder_id()`` method safer and faster for
  Galaxy release_13.06 and later.

* Deprecate and ignore invalid ``deleted`` parameter to
  ``WorkflowClient.get_workflows()``.

* CloudMan: Add method to fetch instance types.

* CloudMan: Update cluster options to reflect change to SLURM.

* BioBlend.objects: Deprecate and ignore invalid ``deleted`` parameter
  to ``ObjWorkflowClient.list()``.

* BioBlend.objects: Add ``paste_content()`` method to ``History`` objects.

* BioBlend.objects: Add ``copy_from_dataset()`` method and ``root_folder``
  property to ``Library`` objects.

* BioBlend.objects: Add ``container`` and ``deleted`` attributes to ``Folder``
  objects.

* BioBlend.objects: Set the ``parent`` attribute of a ``Folder`` object to its
  parent folder object (thanks to John M. Eppley).

* BioBlend.objects: Add ``deleted`` parameter to ``list()`` method
  of libraries and histories.

* BioBlend.objects: Add ``state`` and ``state_details`` attributes to
 ``History`` objects (thanks to Gianmauro Cuccuru).

* BioBlend.objects: Rename ``upload_dataset()`` method to ``upload_file()``
  for ``History`` objects.

* BioBlend.objects: Rename ``input_ids`` and ``output_ids`` attributes of
  ``Workflow`` objects to ``source_ids`` and ``sink_ids`` respectively.

* Add ``run_bioblend_tests.sh`` script (useful for Continuous Integration
  testing).

### BioBlend v0.5.2 - October 17, 2014

* BioBlend.objects: enable email&password auth

* Enable Tool Shed tar ball uploads

* BioBlend.objects: allow deletion of history and library datasets

* BioBlend.objects: fixed library dataset downloads

* Fixed the Tool Shed tool installation method

* Add 'deleted' attribute to DatasetContainer

* Handle `data_type` changes in the Oct 2014 Galaxy release

* Renamed `get_current_history()` to `get_most_recently_used_history()`

* A number of documentation improvements and other small fixes (see
  the commit messages for more details)

### BioBlend v0.5.1 - August 19, 2014

* Fixed url joining problem described in issue #82

* Enabled Travis Continuous Inetgration testing

* Added script to create a user and get its API key

* Deprecated ``create_user()`` method in favor of clearer ``create_remote_user()``.
  Added ``create_local_user()``.

* Skip instead of fail tests when ``BIOBLEND_GALAXY_URL`` and
  ``BIOBLEND_GALAXY_API_KEY`` environment variables are not defined.

* Added export and download to objects API

* Added export/download history

* GalaxyClient: changed ``make_put_request`` to return whole ``requests``
  response object

* Added Tool wrapper to *BioBlend.objects* plus methods to list tools and get one

* Added ``show_tool()`` method to ``ToolClient`` class

* Added ``name``, ``in_panel`` and
  ``trackster`` filters to ``get_tools()``

* Added ``upload_dataset()`` method to ``History`` class.

* Removed ``DataInput`` and ``Tool`` classes for workflow steps. ``Tool`` is to
  be used for running single tools.
