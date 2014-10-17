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
