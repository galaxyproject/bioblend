### BioBlend v - unreleased

* Added support for Python 3.8. Added support for Galaxy release 19.09.
  Dropped support for Galaxy releases 14.10 and 15.01.

### BioBlend v0.13.0 - 2019-08-09

* Dropped support for Python 3.4. Added support for Galaxy releases 19.01 and
  19.05.

* Updated ``requests-toolbelt`` requirement to ``>=0.5.1`` to prevent failing of
  uploads to Galaxy (reported by [m93](https://github.com/mmeier93)).

* Added ``toolshed`` attribute to ``GalaxyInstance`` and made ``toolShed`` an
  alias to it (reported by [Miriam Payá](https://github.com/mpaya)).

* Added ``uninstall_repository_revision()`` method to ``ToolShedClient`` (thanks
  to [Helena Rasche](https://github.com/erasche), reported by
  [Alexander Lenail](https://github.com/alexlenail)).

* Added ``maxwait`` parameter to ``HistoryClient.export_history()`` and
  ``History.export()`` methods.

* Fixed handling of ``type`` parameter in ``HistoryClient.show_history()``
  (thanks to [Marius van den Beek](https://github.com/mvdbeek)).

* Fixed handling of ``deleted`` parameter in ``LibraryClient.get_libraries()``
  (thanks to [Luke Sargent](https://github.com/luke-c-sargent), reported by
  [Katie](https://github.com/emartchenko)).

* Fixed ``LibraryClient.wait_for_dataset()`` when ``maxwait`` or ``interval``
  parameters are of type ``float``.

* Unify JSON-encoding of non-file parameters of POST requests inside
  ``GalaxyClient.make_post_request()``.

* Improvements to tests and documentation (thanks to
  [Helena Rasche](https://github.com/erasche),
  [selten](https://github.com/selten) and
  [Pablo Moreno](https://github.com/pcm32)).

### BioBlend v0.12.0 - 2018-12-17

* Added support for Python 3.7. Added support for Galaxy releases 18.05 and
  18.09.

* Added ``update_library_dataset()`` method to ``LibraryClient`` (thanks to
  Anthony Bretaudeau).

* Added ``preserve_dirs`` and ``tag_using_filenames`` parameters to
  ``upload_file_from_server()`` and ``upload_from_galaxy_filesystem()`` methods
  of ``LibraryClient`` (thanks to Anthony Bretaudeau).

* Removed deprecated ``wait_for_completion`` parameter of
  ``DatasetClient.download_dataset()`` method.

* BioBlend.objects: added ``genome_build`` and ``misc_info`` attributes to
  ``Dataset`` objects. Moved ``deleted`` attribute from ``Dataset`` to
  ``HistoryDatasetAssociation`` and ``LibraryDatasetDatasetAssociation``
  objects. Moved ``purged`` attribute from ``Dataset`` to
  ``HistoryDatasetAssociation`` objects.

* BioBlend.objects: added ``update()`` method to ``LibraryDataset`` (thanks to
  Anthony Bretaudeau).

* Run tests with pytest instead of nose

### BioBlend v0.11.0 - 2018-04-18

* Dropped support for Python 3.3. Added support for Galaxy release 18.01.

* Always wait for terminal state when downloading a dataset.

* Deprecated ``wait_for_completion`` parameter of
  ``DatasetClient.download_dataset()`` method.

* Fixed downloading of datasets receiving a HTTP 500 status code (thanks to
  [Helena Rasche](https://github.com/erasche)).

* Added ``wait_for_dataset()`` method to ``LibraryClient``.

* Added ``verify`` parameter to ``GalaxyInstance.__init__()`` method (thanks to
  Devon Ryan).

* Improvements to tests and documentation.

### BioBlend v0.10.0 - 2017-09-26

* Dropped support for Python 2.6. Added support for Galaxy release 17.09.

* Added ``contents`` parameter to ``FoldersClient.show_folder()`` method
  (thanks to [Helena Rasche](https://github.com/erasche)).

* Exposed the `verify` attribute of `GalaxyInstance` and `ToolShedInstance`
  objects as `__init__()` parameter.

* Added ``create_role()`` method to ``RolesClient`` (thanks to Ashok
  Varadharajan).

* Added ``timeout`` parameter to ``GalaxyClient.__init__()`` method.

* Added ``publish`` parameter to ``import_workflow_dict()`` and
  ``import_workflow_from_local_path()`` methods of ``WorkflowClient`` (thanks to
  Marco Enrico Piras).

* BioBlend.objects: added ``publish`` parameter to
  ``ObjWorkflowClient.import_new()`` method (thanks to Marco Enrico Piras).

* Do not check for mismatching content size when streaming a dataset to file
  (reported by Jorrit Boekel).

* Fixed delete requests when Galaxy uses external authentication (thanks to
  [Helena Rasche](https://github.com/erasche)).

* Fixed retrieval of the API key when a ``GalaxyClient`` object is initialised
  with email and password on Python 3 (thanks to
  [Marius van den Beek](https://github.com/mvdbeek)).

* Documentation improvements.

### BioBlend v0.9.0 - 2017-05-25

* Dropped support for Galaxy releases 14.02, 14.04, 14.06 and 14.08. Added
  support for Python 3.5 and 3.6, and Galaxy releases 16.07, 16.10, 17.01 and
  17.05.

* Deprecated ``import_workflow_json()`` and ``export_workflow_json()`` methods
  of ``WorkflowClient`` in favor of ``import_workflow_dict()`` and
  ``export_workflow_dict()`` (reported by @manabuishii).

* Deprecated ``show_stderr()`` and ``show_stdout()`` methods of
  ``DatasetClient`` in favour of ``JobsClient.show_job()`` with
  ``full_details=True``.

* Added ``install_dependencies()`` method to ``ToolClient`` (thanks to
  [Marius van den Beek](https://github.com/mvdbeek)).

* Added ``reload_data_table()`` method to ``ToolDataClient`` (thanks to
  [Marius van den Beek](https://github.com/mvdbeek)).

* Added ``create_folder()``, ``update_folder()``, ``get_permissions()``,
  ``set_permissions()`` methods to ``FoldersClient`` (thanks to
  [Helena Rasche](https://github.com/erasche)).

* Added ``get_version()`` method to ``ConfigClient`` (thanks to
  [Helena Rasche](https://github.com/erasche)).

* Added ``get_user_apikey()`` method to ``UserClient`` (thanks to
  [Helena Rasche](https://github.com/erasche)).

* Added ``create_quota()``, ``update_quota()``, ``delete_quota()`` and
  ``undelete_quota()`` methods to ``QuotaClient`` (thanks to
  [Helena Rasche](https://github.com/erasche)).

* Added ``purge`` parameter to ``HistoryClient.delete_dataset()`` method.

* Added ``f_email``, ``f_name``, and ``f_any`` parameters to
  ``UserClient.get_users()`` method (thanks to
  [Helena Rasche](https://github.com/erasche)).

* Updated ``WorkflowClient.import_shared_workflow()`` method to use the newer
  Galaxy API request (thanks to @DamCorreia).

* Fixed ``HistoryClient.update_history()`` and ``History.update()`` methods
  when ``name`` parameter is not specified.

* Added warning if content size differs from content-length header in
  ``DatasetClient.download_dataset()``.

* BioBlend.objects: added ``purge`` parameter to
  ``HistoryDatasetAssociation.delete()`` method.

* BioBlend.objects: added ``purged`` attribute to ``Dataset`` objects.

* BioBlend.objects: added ``published`` attribute to ``History`` objects.

* Code refactoring, added tests and documentation improvements.

### BioBlend v0.8.0 - 2016-08-11

* Removed deprecated ``create_user()`` method of ``UserClient``.

* Deprecated ``HistoryClient.download_dataset()`` in favor of
  ``DatasetClient.download_dataset()``.

* Modified ``update_dataset()``, ``update_dataset_collection()`` and
  ``update_history()`` methods of ``HistoryClient`` to return the details
  instead of the status code.

* Modified ``update_dataset()``, ``update_dataset_collection()`` and
  ``update_history()`` methods of ``HistoryClient`` to return the details
  instead of the status code.

* Modified ``GalaxyClient.make_put_request()`` to return the decoded response
  content.

* Added ``install_resolver_dependencies`` parameter to
  ``ToolShedClient.install_repository_revision()``, applicable for Galaxy
  release_16.07 and later (thanks to
  [Marius van den Beek](https://github.com/mvdbeek)).

* Improve ``DatasetClient.download_dataset()`` by downloading the dataset in
  chunks when saving to file (thanks to Jorrit Boekel).

* Added ``bioblend.toolshed.categories.ToolShedCategoryClient``;
  renamed ``bioblend.toolshed.repositories.ToolShedClient`` class to
  ``bioblend.toolshed.repositories.ToolShedRepositoryClient``;
  renamed ``bioblend.toolshed.tools.ToolShedClient`` class to
  ``bioblend.toolshed.tools.ToolShedToolClient``.

* Added ``delete_user()`` method to ``UserClient``.

* BioBlend.objects: added ``update()`` method to ``HistoryDatasetAssociation``.

* BioBlend.objects: added ``annotation`` and ``genome_build`` attributes to
  ``HistoryDatasetAssociation`` objects.

* BioBlend.objects: added ``update()`` method to ``HistoryDatasetAssociation``.

* BioBlend.objects: added ability to create and delete dataset collections
  (thanks to Alex MacLean).

* BioBlend.objects: added dataset collections to the outputs of
  ``Workflow.run()``.

* Added ability to launch Galaxy CloudMan instances into AWS VPC.

* A number of testing tweaks, documentation improvements and minor fixes.

### BioBlend v0.7.0 - 2015-11-02

* BioBlend.objects: enabled import of workflows containing dataset collection
  inputs.

* Implemented APIs for a modern Galaxy workflow APIs (i.e. delayed scheduling).

* Implemented APIs to search Tool Shed repositories and tools.

* Added support for uploading (importing) from FTP (thanks to
  [Helena Rasche](https://github.com/erasche)).

* Added ``to_posix_lines`` and ``space_to_tab`` params to ``upload_file()``,
  ``upload_from_ftp()`` and ``paste_content()`` methods of ``ToolClient``.

* BioBlend.objects: added ``upload_from_ftp()`` method to ``History``.

* Updated the testing framework to work with Galaxy wheels; use TravisCI's
  container infrastructure; test Galaxy release 15.07.

* Updated CloudmanLauncher's ``launch`` method to accept ``subnet_id``
  parameter, for VPC support (thanks to Matthew Ralston).

* Properly pass extra parameters to cloud instance userdata.

* Updated placement finding methods and `get_clusters_pd` method to return a
  dict vs. lists so error messages can be included.

* A numer of documentation improvements and minor updates/fixes (see individual
  commits).

### BioBlend v0.6.1 - 2015-07-27

* BioBlend.objects: renamed ``ObjDatasetClient`` abstract class to
  ``ObjDatasetContainerClient``.

* BioBlend.objects: added ``ABCMeta`` metaclass and ``list()`` method to
  ``ObjClient``.

* BioBlend.objects: added ``io_details`` and ``link_details`` parameters to
  ``ObjToolClient.get()`` method.

* Open port 8800 when launching cloud instances for use by NodeJS proxy for
  Galaxy IPython Interactive Environments.

* When launching cloud instances, propagate error messages back to the called.
  The return types for methods ``create_cm_security_group``, ``create_key_pair``
  in ``CloudManLauncher`` class have changed as a result of this.

### BioBlend v0.6.0 - 2015-06-30

* Added support for Python >= 3.3.

* Added ``get_library_permissions()`` method to ``LibraryClient``.

* Added ``update_group()``, ``get_group_users()``, ``get_group_roles()``,
  ``add_group_user()``, ``add_group_role()``, ``delete_group_user()`` and
  ``delete_group_role()`` methods to ``GroupsClient``.

* Added ``full_details`` parameter to ``JobsClient.show_job()`` (thanks to
  Rossano Atzeni).

* BioBlend.objects: added ``ObjJobClient`` and ``Job`` wrapper (thanks to
  Rossano Atzeni).

* BioBlend.objects: added check to verify that all tools in a workflow are
  installed on the Galaxy instance (thanks to Gianmauro Cuccuru).

* Removed several deprecated parameters: see commits [19e168f](https://github.com/galaxyproject/bioblend/commit/19e168f5342f4c791d37694d7039a85f2669df71)
  and [442ae98](https://github.com/galaxyproject/bioblend/commit/442ae98037be7455d57be15542553dc848d99431).

* Verify SSL certificates by default.

* Added documentation about the Tool Shed and properly link all the docs on
  ReadTheDocs.

* Solidified automated testing by using [tox](https://tox.readthedocs.org/) and
  [flake8](https://gitlab.com/pycqa/flake8).

### BioBlend v0.5.3 - 2015-03-18

* Project source moved to new URL - https://github.com/galaxyproject/bioblend

* Huge improvements to automated testing, tests now run against Galaxy
  release_14.02 and all later versions to ensure backward compatibility
  (see `.travis.yml` for details).

* Many documentation improvements (thanks to
  [Helena Rasche](https://github.com/erasche)).

* Added Galaxy clients for the tool data tables, the roles, and library
  folders (thanks to Anthony Bretaudeau).

* Added method to get the standard error and standard output for the
  job corresponding to a Galaxy dataset (thanks to Anthony Bretaudeau).

* Added ``get_state()`` method to ``JobsClient``.

* Added ``copy_from_dataset()`` method to ``LibraryClient``.

* Added ``create_repository()`` method to ``ToolShedRepositoryClient`` (thanks
  to [Helena Rasche](https://github.com/erasche)).

* Fixed ``DatasetClient.download_dataset()`` for certain proxied Galaxy
  deployments.

* Made ``LibraryClient._get_root_folder_id()`` method safer and faster for
  Galaxy release_13.06 and later.

* Deprecate and ignore invalid ``deleted`` parameter to
  ``WorkflowClient.get_workflows()``.

* CloudMan: added method to fetch instance types.

* CloudMan: updated cluster options to reflect change to SLURM.

* BioBlend.objects: deprecate and ignore invalid ``deleted`` parameter
  to ``ObjWorkflowClient.list()``.

* BioBlend.objects: added ``paste_content()`` method to ``History`` objects.

* BioBlend.objects: added ``copy_from_dataset()`` method and ``root_folder``
  property to ``Library`` objects.

* BioBlend.objects: added ``container`` and ``deleted`` attributes to ``Folder``
  objects.

* BioBlend.objects: the ``parent`` property of a ``Folder`` object is now set to
  its parent folder object (thanks to John M. Eppley).

* BioBlend.objects: added ``deleted`` parameter to ``list()`` method
  of libraries and histories.

* BioBlend.objects: added ``state`` and ``state_details`` attributes to
 ``History`` objects (thanks to Gianmauro Cuccuru).

* BioBlend.objects: renamed ``upload_dataset()`` method to ``upload_file()``
  for ``History`` objects.

* BioBlend.objects: renamed ``input_ids`` and ``output_ids`` attributes of
  ``Workflow`` objects to ``source_ids`` and ``sink_ids`` respectively.

* Add ``run_bioblend_tests.sh`` script (useful for Continuous Integration
  testing).

### BioBlend v0.5.2 - 2014-10-17

* BioBlend.objects: enabled email&password auth

* Enabled Tool Shed tar ball uploads

* BioBlend.objects: implemented deletion of history and library datasets

* BioBlend.objects: fixed library dataset downloads

* Fixed the Tool Shed tool installation method

* Added 'deleted' attribute to DatasetContainer

* Handle `data_type` changes in the Oct 2014 Galaxy release

* Renamed `get_current_history()` to `get_most_recently_used_history()`

* A number of documentation improvements and other small fixes (see
  the commit messages for more details)

### BioBlend v0.5.1 - 2014-08-19

* Fixed url joining problem described in issue #82

* Enabled Travis Continuous Inetgration testing

* Added script to create a user and get its API key

* Deprecated ``create_user()`` method in favor of clearer
  ``create_remote_user()``. Added ``create_local_user()``.

* Skip instead of fail tests when ``BIOBLEND_GALAXY_URL`` and
  ``BIOBLEND_GALAXY_API_KEY`` environment variables are not defined.

* Added export and download to objects API

* Added export/download history

* GalaxyClient: changed ``make_put_request`` to return whole ``requests``
  response object

* Added Tool wrapper to *BioBlend.objects* plus methods to list tools and get
  one.

* Added ``show_tool()`` method to ``ToolClient`` class

* Added ``name``, ``in_panel`` and
  ``trackster`` filters to ``get_tools()``

* Added ``upload_dataset()`` method to ``History`` class.

* Removed ``DataInput`` and ``Tool`` classes for workflow steps. ``Tool`` is to
  be used for running single tools.
