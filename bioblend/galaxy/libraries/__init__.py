"""
Contains possible interactions with the Galaxy Data Libraries
"""
import logging
import time
import warnings

from bioblend.galaxy.client import Client
from bioblend.galaxy.datasets import (
    DatasetTimeoutException,
    TERMINAL_STATES,
)
from bioblend.util import attach_file

log = logging.getLogger(__name__)


class LibraryClient(Client):
    module = 'libraries'

    def __init__(self, galaxy_instance):
        super().__init__(galaxy_instance)

    def create_library(self, name, description=None, synopsis=None):
        """
        Create a data library with the properties defined in the arguments.

        :type name: str
        :param name: Name of the new data library

        :type description: str
        :param description: Optional data library description

        :type synopsis: str
        :param synopsis: Optional data library synopsis

        :rtype: dict
        :return: Details of the created library.
          For example::

            {'id': 'f740ab636b360a70',
             'name': 'Library from bioblend',
             'url': '/api/libraries/f740ab636b360a70'}
        """
        payload = {'name': name}
        if description:
            payload['description'] = description
        if synopsis:
            payload['synopsis'] = synopsis
        return self._post(payload)

    def delete_library(self, library_id):
        """
        Delete a data library.

        :type library_id: str
        :param library_id: Encoded data library ID identifying the library to be
          deleted

        :rtype: dict
        :return: Information about the deleted library

        .. warning::
          Deleting a data library is irreversible - all of the data from the
          library will be permanently deleted.
        """
        return self._delete(id=library_id)

    def _show_item(self, library_id, item_id):
        """
        Get details about a given library item.
        """
        url = '/'.join((self._make_url(library_id, contents=True), item_id))
        return self._get(url=url)

    def delete_library_dataset(self, library_id, dataset_id, purged=False):
        """
        Delete a library dataset in a data library.

        :type library_id: str
        :param library_id: library id where dataset is found in

        :type dataset_id: str
        :param dataset_id: id of the dataset to be deleted

        :type purged: bool
        :param purged: Indicate that the dataset should be purged (permanently
          deleted)

        :rtype: dict
        :return: A dictionary containing the dataset id and whether the dataset
          has been deleted.
          For example::

            {'deleted': True,
             'id': '60e680a037f41974'}
        """
        url = '/'.join((self._make_url(library_id, contents=True), dataset_id))
        return self._delete(payload={'purged': purged}, url=url)

    def update_library_dataset(self, dataset_id, **kwds):
        """
        Update library dataset metadata. Some of the attributes that can be
        modified are documented below.

        :type dataset_id: str
        :param dataset_id: id of the dataset to be deleted

        :type name: str
        :param name: Replace library dataset name with the given string

        :type misc_info: str
        :param misc_info: Replace library dataset misc_info with given string

        :type file_ext: str
        :param file_ext: Replace library dataset extension (must exist in the Galaxy registry)

        :type genome_build: str
        :param genome_build: Replace library dataset genome build (dbkey)

        :type tags: list
        :param tags: Replace library dataset tags with the given list

        :rtype: dict
        :return: details of the updated dataset
        """
        url = '/'.join((self._make_url(), 'datasets', dataset_id))
        return self._patch(payload=kwds, url=url)

    def show_dataset(self, library_id, dataset_id):
        """
        Get details about a given library dataset. The required ``library_id``
        can be obtained from the datasets's library content details.

        :type library_id: str
        :param library_id: library id where dataset is found in

        :type dataset_id: str
        :param dataset_id: id of the dataset to be inspected

        :rtype: dict
        :return: A dictionary containing information about the dataset in the
          library
        """
        return self._show_item(library_id, dataset_id)

    def wait_for_dataset(self, library_id, dataset_id, maxwait=12000, interval=3):
        """
        Wait until the library dataset state is terminal ('ok', 'empty',
        'error', 'discarded' or 'failed_metadata').

        :type library_id: str
        :param library_id: library id where dataset is found in

        :type dataset_id: str
        :param dataset_id: id of the dataset to wait for

        :type maxwait: float
        :param maxwait: Total time (in seconds) to wait for the dataset state to
          become terminal. If the dataset state is not terminal within this
          time, a ``DatasetTimeoutException`` will be thrown.

        :type interval: float
        :param interval: Time (in seconds) to wait between 2 consecutive checks.

        :rtype: dict
        :return: A dictionary containing information about the dataset in the
          library
        """
        assert maxwait >= 0
        assert interval > 0

        time_left = maxwait
        while True:
            dataset = self.show_dataset(library_id, dataset_id)
            state = dataset['state']
            if state in TERMINAL_STATES:
                return dataset
            if time_left > 0:
                log.info("Dataset %s in library %s is in non-terminal state %s. Will wait %i more s", dataset_id, library_id, state, time_left)
                time.sleep(min(time_left, interval))
                time_left -= interval
            else:
                raise DatasetTimeoutException(f"Waited too long for dataset {dataset_id} in library {library_id} to complete")

    def show_folder(self, library_id, folder_id):
        """
        Get details about a given folder. The required ``folder_id`` can be
        obtained from the folder's library content details.

        :type library_id: str
        :param library_id: library id to inspect folders in

        :type folder_id: str
        :param folder_id: id of the folder to be inspected

        :rtype: dict
        :return: Information about the folder
        """
        return self._show_item(library_id, folder_id)

    def _get_root_folder_id(self, library_id):
        """
        Find the root folder (i.e. '/') of a library.

        :type library_id: str
        :param library_id: library id to find root of
        """
        l = self.show_library(library_id=library_id)
        return l['root_folder_id']

    def create_folder(self, library_id, folder_name, description=None, base_folder_id=None):
        """
        Create a folder in a library.

        :type library_id: str
        :param library_id: library id to use

        :type folder_name: str
        :param folder_name: name of the new folder in the data library

        :type description: str
        :param description: description of the new folder in the data library

        :type base_folder_id: str
        :param base_folder_id: id of the folder where to create the new folder.
          If not provided, the root folder will be used

        :rtype: list
        :return: List with a single dictionary containing information about the new folder
        """
        # Get root folder ID if no ID was provided
        if base_folder_id is None:
            base_folder_id = self._get_root_folder_id(library_id)
        # Compose the payload
        payload = {}
        payload['name'] = folder_name
        payload['folder_id'] = base_folder_id
        payload['create_type'] = 'folder'
        if description is not None:
            payload['description'] = description
        return self._post(payload, id=library_id, contents=True)

    def get_folders(self, library_id, folder_id=None, name=None):
        """
        Get all the folders in a library, or select a subset by specifying a
        folder name for filtering.

        :type library_id: str
        :param library_id: library id to use

        :type folder_id: str
        :param folder_id: filter for folder by folder id

          .. deprecated:: 0.16.0
             To get details of a folder for which you know the ID, use the much
             more efficient :meth:`show_folder` instead.

        :type name: str
        :param name: Folder name to filter on. For ``name`` specify the full
                     path of the folder starting from the library's root
                     folder, e.g. ``/subfolder/subsubfolder``.

        :rtype: list
        :return: list of dicts each containing basic information about a folder
        """
        if folder_id is not None:
            warnings.warn(
                'The folder_id parameter is deprecated, use the show_folder() method to view details of a folder for which you know the ID.',
                category=FutureWarning
            )
        if folder_id is not None and name is not None:
            raise ValueError('Provide only one argument between name or folder_id, but not both')
        library_contents = self.show_library(library_id=library_id, contents=True)
        if folder_id is not None:
            folder = next((_ for _ in library_contents if _['type'] == 'folder' and _['id'] == folder_id), None)
            folders = [folder] if folder is not None else []
        elif name is not None:
            folders = [_ for _ in library_contents if _['type'] == 'folder' and _['name'] == name]
        else:
            folders = [_ for _ in library_contents if _['type'] == 'folder']
        return folders

    def get_libraries(self, library_id=None, name=None, deleted=False):
        """
        Get all libraries, or select a subset by specifying optional arguments
        for filtering (e.g. a library name).

        :type library_id: str
        :param library_id: filter for library by library id

          .. deprecated:: 0.16.0
             To get details of a library for which you know the ID, use the much
             more efficient :meth:`show_library` instead.

        :type name: str
        :param name: Library name to filter on.

        :type deleted: bool
        :param deleted: If ``False`` (the default), return only non-deleted
          libraries. If ``True``, return only deleted libraries. If ``None``,
          return both deleted and non-deleted libraries.

        :rtype: list
        :return: list of dicts each containing basic information about a library
        """
        if library_id is not None:
            warnings.warn(
                'The library_id parameter is deprecated, use the show_library() method to view details of a library for which you know the ID.',
                category=FutureWarning
            )
        if library_id is not None and name is not None:
            raise ValueError('Provide only one argument between name or library_id, but not both')
        libraries = self._get(params={"deleted": deleted})
        if library_id is not None:
            library = next((_ for _ in libraries if _['id'] == library_id), None)
            libraries = [library] if library is not None else []
        if name is not None:
            libraries = [_ for _ in libraries if _['name'] == name]
        return libraries

    def show_library(self, library_id, contents=False):
        """
        Get information about a library.

        :type library_id: str
        :param library_id: filter for library by library id

        :type contents: bool
        :param contents: whether to get contents of the library (rather
          than just the library details)

        :rtype: dict
        :return: details of the given library
        """
        return self._get(id=library_id, contents=contents)

    def _do_upload(self, library_id, **keywords):
        """
        Set up the POST request and do the actual data upload to a data library.
        This method should not be called directly but instead refer to the
        methods specific for the desired type of data upload.
        """
        folder_id = keywords.get('folder_id', None)
        if folder_id is None:
            folder_id = self._get_root_folder_id(library_id)
        files_attached = False
        # Compose the payload dict
        payload = {}
        payload['folder_id'] = folder_id
        payload['file_type'] = keywords.get('file_type', 'auto')
        payload['dbkey'] = keywords.get('dbkey', '?')
        payload['create_type'] = 'file'
        if keywords.get("roles", None):
            payload["roles"] = keywords["roles"]
        if keywords.get("link_data_only", None) and keywords['link_data_only'] != 'copy_files':
            payload["link_data_only"] = 'link_to_files'
        payload['tag_using_filenames'] = keywords.get('tag_using_filenames', False)
        if keywords.get('tags'):
            payload['tags'] = keywords['tags']
        payload['preserve_dirs'] = keywords.get('preserve_dirs', False)
        # upload options
        if keywords.get('file_url', None) is not None:
            payload['upload_option'] = 'upload_file'
            payload['files_0|url_paste'] = keywords['file_url']
        elif keywords.get('pasted_content', None) is not None:
            payload['upload_option'] = 'upload_file'
            payload['files_0|url_paste'] = keywords['pasted_content']
        elif keywords.get('server_dir', None) is not None:
            payload['upload_option'] = 'upload_directory'
            payload['server_dir'] = keywords['server_dir']
        elif keywords.get('file_local_path', None) is not None:
            payload['upload_option'] = 'upload_file'
            payload['files_0|file_data'] = attach_file(keywords['file_local_path'])
            files_attached = True
        elif keywords.get("filesystem_paths", None) is not None:
            payload["upload_option"] = "upload_paths"
            payload["filesystem_paths"] = keywords["filesystem_paths"]

        try:
            return self._post(payload, id=library_id, contents=True,
                              files_attached=files_attached)
        finally:
            if payload.get('files_0|file_data', None) is not None:
                payload['files_0|file_data'].close()

    def upload_file_from_url(self, library_id, file_url, folder_id=None,
                             file_type='auto', dbkey='?',
                             tags=None):
        """
        Upload a file to a library from a URL.

        :type library_id: str
        :param library_id: id of the library where to place the uploaded file

        :type file_url: str
        :param file_url: URL of the file to upload

        :type folder_id: str
        :param folder_id: id of the folder where to place the uploaded file.
          If not provided, the root folder will be used

        :type file_type: str
        :param file_type: Galaxy file format name

        :type dbkey: str
        :param dbkey: Dbkey

        :type tags: list
        :param tags: A list of tags to add to the datasets

        :rtype: list
        :return: List with a single dictionary containing information about the LDDA
        """
        return self._do_upload(library_id, file_url=file_url,
                               folder_id=folder_id, file_type=file_type,
                               dbkey=dbkey,
                               tags=tags)

    def upload_file_contents(self, library_id, pasted_content,
                             folder_id=None, file_type='auto', dbkey='?',
                             tags=None):
        """
        Upload pasted_content to a data library as a new file.

        :type library_id: str
        :param library_id: id of the library where to place the uploaded file

        :type pasted_content: str
        :param pasted_content: Content to upload into the library

        :type folder_id: str
        :param folder_id: id of the folder where to place the uploaded file.
          If not provided, the root folder will be used

        :type file_type: str
        :param file_type: Galaxy file format name

        :type dbkey: str
        :param dbkey: Dbkey

        :type tags: list
        :param tags: A list of tags to add to the datasets

        :rtype: list
        :return: List with a single dictionary containing information about the LDDA
        """
        return self._do_upload(library_id, pasted_content=pasted_content,
                               folder_id=folder_id, file_type=file_type,
                               dbkey=dbkey,
                               tags=tags)

    def upload_file_from_local_path(self, library_id, file_local_path,
                                    folder_id=None, file_type='auto', dbkey='?',
                                    tags=None):
        """
        Read local file contents from file_local_path and upload data to a
        library.

        :type library_id: str
        :param library_id: id of the library where to place the uploaded file

        :type file_local_path: str
        :param file_local_path: path of local file to upload

        :type folder_id: str
        :param folder_id: id of the folder where to place the uploaded file.
          If not provided, the root folder will be used

        :type file_type: str
        :param file_type: Galaxy file format name

        :type dbkey: str
        :param dbkey: Dbkey

        :type tags: list
        :param tags: A list of tags to add to the datasets

        :rtype: list
        :return: List with a single dictionary containing information about the LDDA
        """
        return self._do_upload(library_id, file_local_path=file_local_path,
                               folder_id=folder_id, file_type=file_type,
                               dbkey=dbkey,
                               tags=tags)

    def upload_file_from_server(self, library_id, server_dir, folder_id=None,
                                file_type='auto', dbkey='?', link_data_only=None,
                                roles="", preserve_dirs=False, tag_using_filenames=False,
                                tags=None):
        """
        Upload all files in the specified subdirectory of the Galaxy library
        import directory to a library.

        .. note::
          For this method to work, the Galaxy instance must have the
          ``library_import_dir`` option configured in the ``config/galaxy.yml``
          configuration file.

        :type library_id: str
        :param library_id: id of the library where to place the uploaded file

        :type server_dir: str
        :param server_dir: relative path of the subdirectory of
          ``library_import_dir`` to upload. All and only the files (i.e. no
          subdirectories) contained in the specified directory will be
          uploaded

        :type folder_id: str
        :param folder_id: id of the folder where to place the uploaded files.
          If not provided, the root folder will be used

        :type file_type: str
        :param file_type: Galaxy file format name

        :type dbkey: str
        :param dbkey: Dbkey

        :type link_data_only: str
        :param link_data_only: either 'copy_files' (default) or
          'link_to_files'. Setting to 'link_to_files' symlinks instead of
          copying the files

        :type roles: str
        :param roles: ???

        :type preserve_dirs: bool
        :param preserve_dirs: Indicate whether to preserve the directory structure when importing dir

        :type tag_using_filenames: bool
        :param tag_using_filenames: Indicate whether to generate dataset tags
          from filenames.

          .. versionchanged:: 0.14.0
            Changed the default from ``True`` to ``False``.

        :type tags: list
        :param tags: A list of tags to add to the datasets

        :rtype: list
        :return: List with a single dictionary containing information about the LDDA
        """
        return self._do_upload(library_id, server_dir=server_dir,
                               folder_id=folder_id, file_type=file_type,
                               dbkey=dbkey, link_data_only=link_data_only,
                               roles=roles, preserve_dirs=preserve_dirs,
                               tag_using_filenames=tag_using_filenames,
                               tags=tags)

    def upload_from_galaxy_filesystem(self, library_id, filesystem_paths, folder_id=None,
                                      file_type="auto", dbkey="?", link_data_only=None,
                                      roles="", preserve_dirs=False, tag_using_filenames=False,
                                      tags=None):
        """
        Upload a set of files already present on the filesystem of the Galaxy
        server to a library.

        .. note::
          For this method to work, the Galaxy instance must have the
          ``allow_path_paste`` option set to ``true`` in the
          ``config/galaxy.yml`` configuration file.

        :type library_id: str
        :param library_id: id of the library where to place the uploaded file

        :type filesystem_paths: str
        :param filesystem_paths: file paths on the Galaxy server to upload to
          the library, one file per line

        :type folder_id: str
        :param folder_id: id of the folder where to place the uploaded files.
          If not provided, the root folder will be used

        :type file_type: str
        :param file_type: Galaxy file format name

        :type dbkey: str
        :param dbkey: Dbkey

        :type link_data_only: str
        :param link_data_only: either 'copy_files' (default) or
          'link_to_files'. Setting to 'link_to_files' symlinks instead of
          copying the files

        :type roles: str
        :param roles: ???

        :type preserve_dirs: bool
        :param preserve_dirs: Indicate whether to preserve the directory structure when importing dir

        :type tag_using_filenames: bool
        :param tag_using_filenames: Indicate whether to generate dataset tags
          from filenames.

          .. versionchanged:: 0.14.0
            Changed the default from ``True`` to ``False``.

        :type tags: list
        :param tags: A list of tags to add to the datasets

        :rtype: list
        :return: List with a single dictionary containing information about the LDDA
        """
        return self._do_upload(library_id, filesystem_paths=filesystem_paths,
                               folder_id=folder_id, file_type=file_type,
                               dbkey=dbkey, link_data_only=link_data_only,
                               roles=roles, preserve_dirs=preserve_dirs,
                               tag_using_filenames=tag_using_filenames,
                               tags=tags)

    def copy_from_dataset(self, library_id, dataset_id, folder_id=None, message=''):
        """
        Copy a Galaxy dataset into a library.

        :type library_id: str
        :param library_id: id of the library where to place the uploaded file

        :type dataset_id: str
        :param dataset_id: id of the dataset to copy from

        :type folder_id: str
        :param folder_id: id of the folder where to place the uploaded files.
          If not provided, the root folder will be used

        :type message: str
        :param message: message for copying action

        :rtype: dict
        :return: LDDA information
        """
        if folder_id is None:
            folder_id = self._get_root_folder_id(library_id)
        payload = {}
        payload['folder_id'] = folder_id
        payload['create_type'] = 'file'
        payload['from_hda_id'] = dataset_id
        payload['ldda_message'] = message
        return self._post(payload, id=library_id, contents=True)

    def get_library_permissions(self, library_id):
        """
        Get the permissions for a library.

        :type library_id: str
        :param library_id: id of the library

        :rtype: dict
        :return: dictionary with all applicable permissions' values
        """
        url = self._make_url(library_id) + '/permissions'
        return self._get(url=url)

    def get_dataset_permissions(self, dataset_id):
        """
        Get the permissions for a dataset.

        :type dataset_id: str
        :param dataset_id: id of the dataset

        :rtype: dict
        :return: dictionary with all applicable permissions' values
        """
        url = '/'.join((self._make_url(), 'datasets', dataset_id, 'permissions'))
        return self._get(url=url)

    def set_library_permissions(self, library_id, access_in=None,
                                modify_in=None, add_in=None, manage_in=None):
        """
        Set the permissions for a library. Note: it will override all security
        for this library even if you leave out a permission type.

        :type library_id: str
        :param library_id: id of the library

        :type access_in: list
        :param access_in: list of role ids

        :type modify_in: list
        :param modify_in: list of role ids

        :type add_in: list
        :param add_in: list of role ids

        :type manage_in: list
        :param manage_in: list of role ids

        :rtype: dict
        :return: General information about the library
        """
        payload = {}
        if access_in:
            payload['LIBRARY_ACCESS_in'] = access_in
        if modify_in:
            payload['LIBRARY_MODIFY_in'] = modify_in
        if add_in:
            payload['LIBRARY_ADD_in'] = add_in
        if manage_in:
            payload['LIBRARY_MANAGE_in'] = manage_in
        url = self._make_url(library_id) + '/permissions'
        return self._post(payload, url=url)

    def set_dataset_permissions(self, dataset_id, access_in=None,
                                modify_in=None, manage_in=None):
        """
        Set the permissions for a dataset. Note: it will override all security
        for this dataset even if you leave out a permission type.

        :type dataset_id: str
        :param dataset_id: id of the dataset

        :type access_in: list
        :param access_in: list of role ids

        :type modify_in: list
        :param modify_in: list of role ids

        :type manage_in: list
        :param manage_in: list of role ids

        :rtype: dict
        :return: dictionary with all applicable permissions' values
        """
        payload = {}
        if access_in:
            payload['access_ids[]'] = access_in
        if modify_in:
            payload['modify_ids[]'] = modify_in
        if manage_in:
            payload['manage_ids[]'] = manage_in
        # we need here to define an action
        payload['action'] = 'set_permissions'
        url = '/'.join((self._make_url(), 'datasets', dataset_id, 'permissions'))
        return self._post(payload, url=url)
