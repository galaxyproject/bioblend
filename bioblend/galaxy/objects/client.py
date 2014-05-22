"""
Clients for interacting with specific Galaxy entity types.

Classes in this module should not be instantiated directly, but used
via their handles in :class:`~.galaxy_instance.GalaxyInstance`.
"""
import collections, httplib, json, requests, time, abc

import bioblend
import wrappers


# dataset states corresponding to a 'pending' condition
_PENDING_DS_STATES = set(
    ["new", "upload", "queued", "running", "setting_metadata"]
    )
# default chunk size for reading remote data
try:
    import resource
    _CHUNK_SIZE = resource.getpagesize()
except StandardError:
    _CHUNK_SIZE = 4096


def _get_error_info(hda):
    msg = hda.id
    try:
        msg += ' (%s): ' % hda.name
        msg += hda.wrapped['misc_info']
    except StandardError:  # avoid 'error while generating an error report'
        msg += ': error'
    return msg


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

    def _get_container_dataset(self, src, ds_id, ctype=None):
        if isinstance(src, wrappers.DatasetContainer):
            ctype = type(src)
            container_id = src.id
        else:
            assert ctype is not None
            if isinstance(src, collections.Mapping):
                container_id = src['id']
            else:
                container_id = src
        gi_client = getattr(self.gi, ctype.API_MODULE)
        ds_dict = gi_client.show_dataset(container_id, ds_id)
        return ctype.DS_TYPE(ds_dict, container_id, gi=self.obj_gi)


class ObjDatasetClient(ObjClient):

    @abc.abstractmethod
    def _dataset_stream_url(self, dataset):
        pass

    def get_datasets(self, src, name=None):
        """
        Get all datasets contained by the given dataset container.

        :type src: :class:`~.wrappers.History` or :class:`~.wrappers.Library`
        :param src: the dataset container

        :type name: str
        :param name: return only datasets with this name

        :rtype: list of :class:`~.wrappers.LibraryDataset` or list of
          :class:`~.wrappers.HistoryDatasetAssociation`
        :return: datasets associated with the given container

        .. note::

          when filtering library datasets by name, specify their full
          paths starting from the library's root folder, e.g.,
          ``/seqdata/reads.fastq``.  Full paths are available through
          the ``content_infos`` attribute of
          :class:`~.wrappers.Library` objects.
        """
        if not isinstance(src, wrappers.DatasetContainer):
            self._error('not a history or library object', err_type=TypeError)
        if name is None:
            ds_ids = src.dataset_ids
        else:
            ds_ids = [_.id for _ in src.content_infos if _.name == name]
        return [self._get_container_dataset(src, _, ctype=type(src))
                for _ in ds_ids]

    def get_stream(self, dataset, chunk_size=_CHUNK_SIZE):
        """
        Open ``dataset`` for reading and return an iterator over its contents.

        :type dataset:
          :class:`~.wrappers.HistoryDatasetAssociation`
        :param dataset: the dataset to read from

        :type chunk_size: int
        :param chunk_size: read this amount of bytes at a time
        """
        url = self._dataset_stream_url(dataset)
        params = {'key': self.gi.key}
        if isinstance(dataset, wrappers.LibraryDataset):
            params['ldda_ids%5B%5D'] = dataset.id
        get_options = {
            'verify': self.gi.verify,
            'params': params,
            'stream': True,
            }
        r = requests.get(url, **get_options)
        r.raise_for_status()
        return r.iter_content(chunk_size)  # FIXME: client can't close r


class ObjLibraryClient(ObjDatasetClient):
    """
    Interacts with Galaxy libraries.
    """
    def __init__(self, obj_gi):
        super(ObjLibraryClient, self).__init__(obj_gi)

    def _dataset_stream_url(self, dataset):
        base_url = self.gi._make_url(self.gi.libraries)
        return "%s/datasets/download/uncompressed" % base_url

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
        return self.get_dataset(library, ds_info['id'])

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
            self.get_dataset(library, ds_info['id']) for ds_info in res
            ]
        library.refresh()
        return new_datasets

    def get_dataset(self, src, ds_id):
        """
        Retrieve the library dataset corresponding to the given id.

        :rtype: :class:`~.wrappers.LibraryDataset`
        :return: the library dataset corresponding to ``id_``
        """
        return self._get_container_dataset(src, ds_id, wrappers.Library)

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

    POLLING_INTERVAL = wrappers.HistoryDatasetAssociation.POLLING_INTERVAL

    def __init__(self, obj_gi):
        super(ObjHistoryClient, self).__init__(obj_gi)

    def _dataset_stream_url(self, dataset):
        base_url = self.gi._make_url(
            self.gi.histories, module_id=dataset.container_id, contents=True
            )
        return "%s/%s/display" % (base_url, dataset.id)

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

    def update(self, history, name=None, annotation=None):
        """
        Update history metadata with the given name and annotation.
        """
        res = self.gi.histories.update_history(
            history.id, name=name, annotation=annotation
            )
        if res != httplib.OK:
            self._error('update_history: failed to update %r' % (history.id,))
        return self.get(history.id)

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

    #-- history contents --

    def import_dataset(self, history, lds):
        """
        Import a dataset into the history from a library.

        :type history: :class:`~.wrappers.History`
        :param history: target history

        :type lds: :class:`~.wrappers.LibraryDataset`
        :param lds: the library dataset to import

        :rtype:
          :class:`~.wrappers.HistoryDatasetAssociation`
        :return: the imported history dataset
        """
        if not history.is_mapped:
            self._error('history is not mapped to a Galaxy object')
        if not isinstance(lds, wrappers.LibraryDataset):
            self._error('lds is not a LibraryDataset', err_type=TypeError)
        # upload_dataset_from_library returns a dict with the unencoded id
        # to get the encoded id, we have to detect the new entry by diff
        old_ids = set(history.dataset_ids)
        res = self.gi.histories.upload_dataset_from_library(history.id, lds.id)
        if not isinstance(res, collections.Mapping):
            self._error(
                'upload_dataset_from_library: unexpected reply: %r' % (res,)
                )
        history.refresh()
        diff = set(history.dataset_ids) - old_ids
        if len(diff) != 1:
            self._error('cannot retrieve hda id')
        return self.get_dataset(history, diff.pop())

    def get_dataset(self, src, ds_id):
        """
        Retrieve the history dataset corresponding to the given id.

        :rtype:
          :class:`~.wrappers.HistoryDatasetAssociation`
        :return: the history dataset corresponding to ``id_``
        """
        return self._get_container_dataset(src, ds_id, wrappers.History)

    def wait(self, datasets, polling_interval=POLLING_INTERVAL,
             break_on_error=True):
        """
        Wait for datasets to come out of the pending states.

        :type datasets: :class:`~collections.Iterable` of
          :class:`~.wrappers.HistoryDatasetAssociation`
        :param datasets: history datasets

        :type polling_interval: float
        :param polling_interval: polling interval in seconds

        :type break_on_error: bool
        :param break_on_error: if :obj:`True`, break as soon as at least
          one of the datasets is in the 'error' state.

        .. warning::

          This is a blocking operation that can take a very long time.
          Also, note that this method does not return anything;
          however, each input dataset is refreshed (possibly multiple
          times) during the execution.
        """
        self.log.info('waiting for datasets')
        datasets = [_ for _ in datasets if _.state in _PENDING_DS_STATES]
        while datasets:
            time.sleep(polling_interval)
            for i in xrange(len(datasets)-1, -1, -1):
                ds = datasets[i]
                ds.refresh()
                self.log.info('{0.id}: {0.state}'.format(ds))
                if break_on_error and ds.state == 'error':
                    self._error(_get_error_info(ds))
                if ds.state not in _PENDING_DS_STATES:
                    del datasets[i]


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

    def export(self, id_):
        """
        Export a re-importable representation of a workflow.

        :type id_: str
        :param id_: workflow id

        :rtype: dict
        :return: a JSON-serializable dump of the workflow identified by ``id_``
        """
        return self.gi.workflows.export_workflow_json(id_)

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

    def run(self, workflow, input_map, history, params=None,
            import_inputs=False, replacement_params=None):
        """
        Run ``workflow`` in the current Galaxy instance.

        :type workflow: :class:`~.wrappers.Workflow`
        :param workflow: the workflow that should be run

        :type input_map: dict
        :param input_map: a mapping from workflow input labels to
          datasets, e.g.: ``dict(zip(workflow.input_labels,
          library.get_datasets()))``

        :type history: :class:`~.wrappers.History` or str
        :param history: either a valid history object (results will be
          stored there) or a string (a new history will be created with
          the given name).

        :type params: :class:`~collections.Mapping`
        :param params: parameter settings for workflow steps (see below)

        :type import_inputs: bool
        :param import_inputs: If :obj:`True`, workflow inputs will be
          imported into the history; if :obj:`False`, only workflow
          outputs will be visible in the history.

        :type replacement_params: :class:`~collections.Mapping`
        :param replacement_params: pattern-based replacements for
          post-job actions (see below)

        :rtype: tuple
        :return: list of output datasets, output history

        The ``params`` dict should be structured as follows::

          PARAMS = {STEP_ID: PARAM_DICT, ...}
          PARAM_DICT = {NAME: VALUE, ...}

        For backwards compatibility, the following (deprecated) format is
        also supported::

          PARAMS = {TOOL_ID: PARAM_DICT, ...}

        in which case PARAM_DICT affects all steps with the given tool id.
        If both by-tool-id and by-step-id specifications are used, the
        latter takes precedence.

        Finally (again, for backwards compatibility), PARAM_DICT can also
        be specified as::

          PARAM_DICT = {'param': NAME, 'value': VALUE}

        Note that this format allows only one parameter to be set per step.

        Example: set 'a' to 1 for the third workflow step::

          params = {workflow.steps[2].id: {'a': 1}}

        The ``replacement_params`` dict should map parameter names in
        post-job actions (PJAs) to their runtime values.  For
        instance, if the final step has a PJA like the following::

          {u'RenameDatasetActionout_file1': {
             u'action_arguments': {u'newname': u'${output}'},
             u'action_type': u'RenameDatasetAction',
             u'output_name': u'out_file1'}}

        then the following renames the output dataset to 'foo'::

          replacement_params = {'output': 'foo'}

        see also `this thread
        <http://lists.bx.psu.edu/pipermail/galaxy-dev/2011-September/006875.html>`_

        .. warning::
          This is an asynchronous operation: when the method returns,
          the output datasets and history will most likely **not** be
          in their final state.  Use :meth:`ObjHistoryClient.wait` if
          you want to block until they're ready.
        """
        if not workflow.is_mapped:
            self._error('workflow is not mapped to a Galaxy object')
        if not workflow.is_runnable:
            self._error('workflow has missing tools: %s' % ', '.join(
                '%s[%s]' % (workflow.steps[_].tool_id, _)
                for _ in workflow.missing_ids
                ))
        ds_map = workflow.convert_input_map(input_map)
        kwargs = {
            'params': params,
            'import_inputs_to_history': import_inputs,
            'replacement_params': replacement_params,
            }
        if isinstance(history, wrappers.History):
            try:
                kwargs['history_id'] = history.id
            except AttributeError:
                self._error('history does not have an id')
        elif not isinstance(history, basestring):
            self._error(
                'history must be either a history wrapper or a string',
                err_type=TypeError,
                )
        else:
            kwargs['history_name'] = history
        res = self.gi.workflows.run_workflow(workflow.id, ds_map, **kwargs)
        res = self._get_dict('run_workflow', res)
        # res structure: {'history': HIST_ID, 'outputs': [DS_ID, DS_ID, ...]}
        out_hist = self.obj_gi.histories.get(res['history'])
        assert set(res['outputs']).issubset(out_hist.dataset_ids)
        out_dss = [out_hist.get_dataset(_) for _ in res['outputs']]
        return out_dss, out_hist

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
