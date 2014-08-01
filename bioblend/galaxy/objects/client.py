"""
Clients for interacting with specific Galaxy entity types.

Classes in this module should not be instantiated directly, but used
via their handles in :class:`~.galaxy_instance.GalaxyInstance`.
"""
import collections, json, abc

import bioblend
import wrappers


class ObjClient(object):

    @abc.abstractmethod
    def __init__(self, obj_gi):
        self.obj_gi = obj_gi
        self.gi = self.obj_gi.gi
        self.log = bioblend.log

    @abc.abstractmethod
    def get_previews(self, name=None, **kwargs):
        """
        Get object previews (listings).

        Previews model entity summaries provided by REST collection
        URIs, e.g., ``http://host:port/api/libraries``.  Being the
        most lightweight objects associated to the various entities,
        these are the ones that should be used to retrieve basic info
        such as id and name.

        :type name: str
        :param name: return only objects with this name

        Optional boolean kwargs for specific object types:

        ``deleted`` (libraries and histories)
          if :obj:`True`, return only deleted objects

        ``published`` (workflows)
          if :obj:`True`, return published workflows

        :rtype: list of :class:`~.wrappers.Preview`
        """
        pass

    def _select_ids(self, id_=None, name=None):
        """
        Return the id list that corresponds to the given id or name info.
        """
        if id_ is None and name is None:
            self._error('neither id nor name provided', err_type=TypeError)
        if id_ is not None and name is not None:
            self._error('both id and name provided', err_type=TypeError)
        if id_ is None:
            return [_.id for _ in self.get_previews(name=name)]
        else:
            return [id_]

    #-- helpers --
    def _error(self, msg, err_type=RuntimeError):
        self.log.error(msg)
        raise err_type(msg)

    def _get_dict(self, meth_name, reply):
        if reply is None:
            self._error('%s: no reply' % meth_name)
        elif isinstance(reply, collections.Mapping):
            return reply
        try:
            return reply[0]
        except (TypeError, IndexError):
            self._error('%s: unexpected reply: %r' % (meth_name, reply))


class ObjDatasetClient(ObjClient):

    def _get_container(self, id_, ctype):
        show_fname = 'show_%s' % ctype.__name__.lower()
        gi_client = getattr(self.gi, ctype.API_MODULE)
        show_f = getattr(gi_client, show_fname)
        res = show_f(id_)
        cdict = self._get_dict(show_fname, res)
        cdict['id'] = id_  # overwrite unencoded id
        c_infos = show_f(id_, contents=True)
        if not isinstance(c_infos, collections.Sequence):
            self._error('%s: unexpected reply: %r' % (show_fname, c_infos))
        c_infos = [ctype.CONTENT_INFO_TYPE(_) for _ in c_infos]
        return ctype(cdict, content_infos=c_infos, gi=self.obj_gi)


class ObjLibraryClient(ObjDatasetClient):
    """
    Interacts with Galaxy libraries.
    """
    def __init__(self, obj_gi):
        super(ObjLibraryClient, self).__init__(obj_gi)

    def create(self, name, description=None, synopsis=None):
        """
        Create a data library with the properties defined in the arguments.

        Requires ``allow_library_path_paste = True`` to be set in
        Galaxy's configuration file ``universe_wsgi.ini``.

        :rtype: :class:`~.wrappers.Library`
        :return: the library just created
        """
        res = self.gi.libraries.create_library(name, description, synopsis)
        lib_info = self._get_dict('create_library', res)
        return self.get(lib_info['id'])

    def get(self, id_):
        """
        Retrieve the data library corresponding to the given id.

        :rtype: :class:`~.wrappers.Library`
        :return: the library corresponding to ``id_``
        """
        return self._get_container(id_, wrappers.Library)

    def get_previews(self, name=None, deleted=False):
        dicts = self.gi.libraries.get_libraries(name=name, deleted=deleted)
        return [wrappers.LibraryPreview(_, gi=self.obj_gi) for _ in dicts]

    def list(self, name=None):
        """
        Get libraries owned by the user of this Galaxy instance.

        :type name: str
        :param name: return only libraries with this name

        :rtype: list of :class:`~.wrappers.Library`
        """
        dicts = self.gi.libraries.get_libraries(name=name)
        return [self.get(_['id']) for _ in dicts if not _['deleted']]

    def delete(self, id_=None, name=None):
        """
        Delete the library with the given id or name.

        Note that the same name can map to multiple libraries.

        .. warning::
          Deleting a data library is irreversible - all of the data from
          the library will be permanently deleted.
        """
        for id_ in self._select_ids(id_=id_, name=name):
            res = self.gi.libraries.delete_library(id_)
            if not isinstance(res, collections.Mapping):
                self._error('delete_library: unexpected reply: %r' % (res,))

    #-- library contents --

    def __pre_upload(self, library, folder):
        if not library.is_mapped:
            self._error('library is not mapped to a Galaxy object')
        return None if folder is None else folder.id

    def __post_upload(self, library, meth_name, reply):
        ds_info = self._get_dict(meth_name, reply)
        return library.get_dataset(ds_info['id'])

    def upload_data(self, library, data, folder=None, **kwargs):
        """
        Upload data to a Galaxy library.

        :type library: :class:`~.wrappers.Library`
        :param library: a library object

        :type data: str
        :param data: dataset contents

        :type folder: :class:`~.wrappers.Folder`
        :param folder: a folder object, or :obj:`None` to upload to
          the root folder

        :rtype: :class:`~.wrappers.LibraryDataset`
        :return: the dataset object that represents the uploaded content

        Optional keyword arguments: ``file_type``, ``dbkey``.
        """
        fid = self.__pre_upload(library, folder)
        res = self.gi.libraries.upload_file_contents(
            library.id, data, folder_id=fid, **kwargs
            )
        new_dataset = self.__post_upload(library, 'upload_file_contents', res)
        library.refresh()
        return new_dataset

    def upload_from_url(self, library, url, folder=None, **kwargs):
        """
        Upload data to a Galaxy library from the given URL.

        :type url: str
        :param url: URL from which data should be read

        See :meth:`.upload_data` for info on other params.
        """
        fid = self.__pre_upload(library, folder)
        res = self.gi.libraries.upload_file_from_url(
            library.id, url, fid, **kwargs
            )
        new_dataset = self.__post_upload(library, 'upload_file_from_url', res)
        library.refresh()
        return new_dataset

    def upload_from_local(self, library, path, folder=None, **kwargs):
        """
        Upload data to a Galaxy library from a local file.

        :type path: str
        :param path: local file path from which data should be read

        See :meth:`.upload_data` for info on other params.
        """
        fid = self.__pre_upload(library, folder)
        res = self.gi.libraries.upload_file_from_local_path(
            library.id, path, fid, **kwargs
            )
        new_dataset = self.__post_upload(
            library, 'upload_file_from_local_path', res
            )
        library.refresh()
        return new_dataset

    def upload_from_galaxy_fs(self, library, paths, folder=None, **kwargs):
        """
        Upload data to a Galaxy library from filesystem paths on the server.

        :type paths: str or :class:`~collections.Iterable` of str
        :param paths: server-side file paths from which data should be read

        See :meth:`.upload_data` for info on other params; in
        addition, this method accepts a ``link_data_only`` keyword
        argument that, if set, instructs Galaxy to link files instead
        of copying them.
        """
        fid = self.__pre_upload(library, folder)
        if isinstance(paths, basestring):
            paths = (paths,)
        paths = '\n'.join(paths)
        res = self.gi.libraries.upload_from_galaxy_filesystem(
            library.id, paths, folder_id=fid, **kwargs
            )
        if res is None:
            self._error('upload_from_galaxy_filesystem: no reply')
        if not isinstance(res, collections.Sequence):
            self._error(
                'upload_from_galaxy_filesystem: unexpected reply: %r' % (res,)
                )
        new_datasets = [
            library.get_dataset(ds_info['id']) for ds_info in res
            ]
        library.refresh()
        return new_datasets

    def create_folder(self, library, name, description=None, base_folder=None):
        """
        Create a folder in the given library.

        :type library: :class:`~.wrappers.Library`
        :param library: a library object

        :type name: str
        :param name: folder name

        :type description: str
        :param description: optional folder description

        :type base_folder: :class:`~.wrappers.Folder`
        :param base_folder: parent folder, or :obj:`None` to create in
          the root folder

        :rtype: :class:`~.wrappers.Folder`
        :return: the folder just created
        """
        bfid = None if base_folder is None else base_folder.id
        res = self.gi.libraries.create_folder(
            library.id, name, description=description, base_folder_id=bfid,
            )
        folder_info = self._get_dict('create_folder', res)
        library.refresh()
        return self.get_folder(library, folder_info['id'])

    def get_folder(self, library, f_id):
        """
        Retrieve the folder corresponding to the given id.

        :rtype: :class:`~.wrappers.Folder`
        :return: the folder corresponding to ``id_``
        """
        f_dict = self.gi.libraries.show_folder(library.id, f_id)
        return wrappers.Folder(f_dict, library.id, gi=self.obj_gi)


class ObjHistoryClient(ObjDatasetClient):
    """
    Interacts with Galaxy histories.
    """

    def __init__(self, obj_gi):
        super(ObjHistoryClient, self).__init__(obj_gi)

    def create(self, name=None):
        """
        Create a new Galaxy history, optionally setting its name.

        :rtype: :class:`~.wrappers.History`
        :return: the history just created
        """
        res = self.gi.histories.create_history(name=name)
        hist_info = self._get_dict('create_history', res)
        return self.get(hist_info['id'])

    def get(self, id_):
        """
        Retrieve the history corresponding to the given id.

        :rtype: :class:`~.wrappers.History`
        :return: the history corresponding to ``id_``
        """
        return self._get_container(id_, wrappers.History)

    def get_previews(self, name=None, deleted=False):
        dicts = self.gi.histories.get_histories(name=name, deleted=deleted)
        return [wrappers.HistoryPreview(_, gi=self.obj_gi) for _ in dicts]

    def list(self, name=None):
        """
        Get histories owned by the user of this Galaxy instance.

        :type name: str
        :param name: return only histories with this name

        :rtype: list of :class:`~.wrappers.History`
        """
        dicts = self.gi.histories.get_histories(name=name)
        return [self.get(_['id']) for _ in dicts]

    def delete(self, id_=None, name=None, purge=False):
        """
        Delete the history with the given id or name.

        Note that the same name can map to multiple histories.

        :type purge: bool
        :param purge: if :obj:`True`, also purge the history (requires
          ``allow_user_dataset_purge = True`` to be set in Galaxy's
          configuration file ``universe_wsgi.ini``)
        """
        for id_ in self._select_ids(id_=id_, name=name):
            res = self.gi.histories.delete_history(id_, purge=purge)
            if not isinstance(res, collections.Mapping):
                self._error('delete_history: unexpected reply: %r' % (res,))


class ObjWorkflowClient(ObjClient):
    """
    Interacts with Galaxy workflows.
    """

    def __init__(self, obj_gi):
        super(ObjWorkflowClient, self).__init__(obj_gi)

    def import_new(self, src):
        """
        Imports a new workflow into Galaxy.

        :type src: dict or str
        :param src: deserialized (dictionary) or serialized (str) JSON
          dump of the workflow (this is normally obtained by exporting
          a workflow from Galaxy).

        :rtype: :class:`~.wrappers.Workflow`
        :return: the workflow just imported
        """
        if isinstance(src, collections.Mapping):
            wf_dict = src
        else:
            try:
                wf_dict = json.loads(src)
            except (TypeError, ValueError):
                self._error('src not supported: %r' % (src,))
        wf_info = self.gi.workflows.import_workflow_json(wf_dict)
        return self.get(wf_info['id'])

    def import_shared(self, id_):
        """
        Imports a shared workflow to the user's space.

        :type id_: str
        :param id_: workflow id

        :rtype: :class:`~.wrappers.Workflow`
        :return: the workflow just imported
        """
        wf_info = self.gi.workflows.import_shared_workflow(id_)
        return self.get(wf_info['id'])

    def get(self, id_):
        """
        Retrieve the workflow corresponding to the given id.

        :rtype: :class:`~.wrappers.Workflow`
        :return: the workflow corresponding to ``id_``
        """
        res = self.gi.workflows.show_workflow(id_)
        wf_dict = self._get_dict('show_workflow', res)
        return wrappers.Workflow(wf_dict, gi=self.obj_gi)

    # the 'deleted' option is not available for workflows
    def get_previews(self, name=None, published=False):
        dicts = self.gi.workflows.get_workflows(
            name=name, published=published
            )
        return [wrappers.WorkflowPreview(_, gi=self.obj_gi) for _ in dicts]

    def list(self, name=None, deleted=False, published=False):
        """
        Get workflows owned by the user of this Galaxy instance.

        :type name: str
        :param name: return only workflows with this name
        :type published: bool
        :param published: return published workflows

        :rtype: list of :class:`~.wrappers.Workflow`
        """
        dicts = self.gi.workflows.get_workflows(
            name=name, deleted=deleted, published=published
            )
        return [self.get(_['id']) for _ in dicts]

    def delete(self, id_=None, name=None):
        """
        Delete the workflow with the given id or name.

        Note that the same name can map to multiple workflows.

        .. warning::
          Deleting a workflow is irreversible - all of the data from
          the workflow will be permanently deleted.
        """
        for id_ in self._select_ids(id_=id_, name=name):
            res = self.gi.workflows.delete_workflow(id_)
            if not isinstance(res, basestring):
                self._error('delete_workflow: unexpected reply: %r' % (res,))


class ObjToolClient(ObjClient):
    """
    Interacts with Galaxy tools.
    """
    def __init__(self, obj_gi):
        super(ObjToolClient, self).__init__(obj_gi)

    def get(self, id_):
        """
        Retrieve the tool corresponding to the given id.

        :rtype: :class:`~.wrappers.Tool`
        :return: the tool corresponding to ``id_``
        """
        res = self.gi.tools.show_tool(id_)
        tool_dict = self._get_dict('show_tool', res)
        return wrappers.Tool(tool_dict, gi=self.obj_gi)

    def get_previews(self, name=None, trackster=None):
        """
        Get the list of tools installed on the Galaxy instance.

        :type name: str
        :param name: return only tools with this name

        :type trackster: boolean
        :param trackster: if True, only tools that are compatible with
          Trackster are returned

        :rtype: list of :class:`~.wrappers.Tool`
        """
        dicts = self.gi.tools.get_tools(name=name, trackster=trackster)
        return [wrappers.Tool(_, gi=self.obj_gi) for _ in dicts]

    # the 'deleted' option is not available for tools
    def list(self, name=None, trackster=None):
        """
        Get the list of tools installed on the Galaxy instance.

        :type name: str
        :param name: return only tools with this name

        :type trackster: boolean
        :param trackster: if True, only tools that are compatible with
          Trackster are returned

        :rtype: list of :class:`~.wrappers.Tool`
        """
        dicts = self.gi.tools.get_tools(name=name, trackster=trackster)
        return [self.get(_['id']) for _ in dicts]
