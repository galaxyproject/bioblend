
import collections
import httplib
import json
import requests
import time

import wrappers

class ObjClient(object):
    def __init__(self, ginstance):
        self.gi = ginstance
        self.log = ginstance.log

    #-- helpers --
    def __error(self, msg, err_type=RuntimeError):
        self.log.error(msg)
        raise err_type(msg)

    def __get_dict(self, meth_name, reply):
        if reply is None:
            self.__error('%s: no reply' % meth_name)
        elif isinstance(reply, collections.Mapping):
            return reply
        try:
            return reply[0]
        except (TypeError, IndexError):
            self.__error('%s: unexpected reply: %r' % (meth_name, reply))

    def __get_container(self, id_, ctype):
        show_fname = 'show_%s' % ctype.__name__.lower()
        gi_client = getattr(self.gi, ctype.API_MODULE)
        show_f = getattr(gi_client, show_fname)
        res = show_f(id_)
        cdict = self.__get_dict(show_fname, res)
        cdict['id'] = id_  # overwrite unencoded id
        ds_infos = show_f(id_, contents=True)
        if not isinstance(ds_infos, collections.Sequence):
            self.__error('%s: unexpected reply: %r' % (show_fname, ds_infos))
        f_ids, ds_ids = [], []
        for di in ds_infos:
            if di['type'] == 'folder':
                f_ids.append(di['id'])
            else:
                ds_ids.append(di['id'])
        kwargs = {'dataset_ids': ds_ids}
        if issubclass(ctype, wrappers.Library):
            kwargs['folder_ids'] = f_ids
        return ctype(cdict, **kwargs)


    def __get_container_dataset(self, src, ds_id, ctype=None):
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
        return ctype.DS_TYPE(ds_dict, container_id)

    def get_datasets(self, src):
        """
        Get all datasets contained by the given dataset container.

        :type src: :class:`~bioblend.galaxy.objects.wrappers.History`
          or :class:`~bioblend.galaxy.objects.wrappers.Library`
        :param src: the dataset container

        :rtype: list of
          :class:`~bioblend.galaxy.objects.wrappers.LibraryDataset` or list of
          :class:`~bioblend.galaxy.objects.wrappers.HistoryDatasetAssociation`
        :return: datasets associated with the given container
        """
        if not isinstance(src, wrappers.DatasetContainer):
            self.__error('not a history or library object', err_type=TypeError)
        return [self.__get_container_dataset(src, _, ctype=type(src))
                for _ in src.dataset_ids]


class ObjLibraryClient(ObjClient):

    def create(self, name, description=None, synopsis=None):
        """
        Create a data library with the properties defined in the arguments.

        Requires ``allow_library_path_paste = True`` to be set in
        Galaxy's configuration file ``universe_wsgi.ini``.

        :rtype: :class:`~bioblend.galaxy.objects.wrappers.Library`
        :return: the library just created
        """
        res = self.gi.libraries.create_library(name, description, synopsis)
        lib_info = self.__get_dict('create_library', res)
        return self.get(lib_info['id'])

    def get(self, id_):
        """
        Retrieve the data library corresponding to the given id.

        :rtype: :class:`~bioblend.galaxy.objects.wrappers.Library`
        :return: the library corresponding to ``id_``
        """
        return self.__get_container(id_, wrappers.Library)

    def get_previews(self, name=None, deleted=False):
        """
        Get library previews for the user of this Galaxy instance.

        :type name: str
        :param name: return only libraries with this name

        :type deleted: bool
        :param deleted: if :obj:`True`, return only deleted libraries

        :rtype: list of
          :class:`~bioblend.galaxy.objects.wrappers.LibraryPreview`
        """
        dicts = self.gi.libraries.get_libraries(name=name, deleted=deleted)
        return [wrappers.LibraryPreview(_) for _ in dicts]

    def list(self, name=None):
        """
        Get libraries owned by the user of this Galaxy instance.

        :type name: str
        :param name: return only libraries with this name

        :rtype: list of :class:`~bioblend.galaxy.objects.wrappers.Library`
        """
        dicts = self.gi.libraries.get_libraries(name=name)
        return [self.get(_['id']) for _ in dicts]

    def delete(self, library):
        """
        Delete the given data library.

        .. warning::
          Deleting a data library is irreversible - all of the data from
          the library will be permanently deleted.
        """
        if not library.is_mapped:
            self.__error('library is not mapped to a Galaxy object')
        res = self.gi.libraries.delete_library(library.id)
        if not isinstance(res, collections.Mapping):
            self.__error('delete_library: unexpected reply: %r' % (res,))
        library.unmap()

    #-- library contents --

    def __pre_upload(self, library, folder):
        if not library.is_mapped:
            self.__error('library is not mapped to a Galaxy object')
        return None if folder is None else folder.id

    def __post_upload(self, library, meth_name, reply):
        ds_info = self.__get_dict(meth_name, reply)
        return self.get_dataset(library, ds_info['id'])


    def upload_data(self, library, data, folder=None, **kwargs):
        """
        Upload data to a Galaxy library.

        :type library: :class:`~bioblend.galaxy.objects.wrappers.Library`
        :param library: a library object

        :type data: str
        :param data: dataset contents

        :type folder: :class:`~bioblend.galaxy.objects.wrappers.Folder`
        :param folder: a folder object, or :obj:`None` to upload to
          the root folder

        :rtype: :class:`~bioblend.galaxy.objects.wrappers.LibraryDataset`
        :return: the dataset object that represents the uploaded content

        Optional keyword arguments: ``file_type``, ``dbkey``.
        """
        fid = self.__pre_upload(library, folder)
        res = self.gi.libraries.upload_file_contents(
            library.id, data, folder_id=fid, **kwargs
            )
        return self.__post_upload(library, 'upload_file_contents', res)

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
        return self.__post_upload(library, 'upload_file_from_url', res)

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
        return self.__post_upload(library, 'upload_file_from_local_path', res)

    def upload_from_galaxy_fs(self, library, paths, folder=None, **kwargs):
        """
        Upload data to a Galaxy library from filesystem paths on the server.

        :type paths: str or :class:`~collections.Iterable` of str
        :param paths: server-side file paths from which data should be read

        See :meth:`.upload_data` for info on other params.
        """
        fid = self.__pre_upload(library, folder)
        if isinstance(paths, basestring):
            paths = (paths,)
        paths = '\n'.join(paths)
        res = self.gi.libraries.upload_from_galaxy_filesystem(
            library.id, paths, folder_id=fid, **kwargs
            )
        if res is None:
            self.__error('upload_from_galaxy_filesystem: no reply')
        if not isinstance(res, collections.Sequence):
            self.__error(
                'upload_from_galaxy_filesystem: unexpected reply: %r' % (res,)
                )
        return [self.get_dataset(library, ds_info['id'])
                for ds_info in res]

    def get_dataset(self, src, ds_id):
        """
        Retrieve the library dataset corresponding to the given id.

        :rtype: :class:`~bioblend.galaxy.objects.wrappers.LibraryDataset`
        :return: the library dataset corresponding to ``id_``
        """
        return self.__get_container_dataset(src, ds_id, wrappers.Library)

    def create_folder(self, library, name, description=None, base_folder=None):
        """
        Create a folder in the given library.

        :type library: :class:`~bioblend.galaxy.objects.wrappers.Library`
        :param library: a library object

        :type name: str
        :param name: folder name

        :type description: str
        :param description: optional folder description

        :type base_folder: :class:`~bioblend.galaxy.objects.wrappers.Folder`
        :param base_folder: parent folder, or :obj:`None` to create in
          the root folder

        :rtype: :class:`~bioblend.galaxy.objects.wrappers.Folder`
        :return: the folder just created
        """
        bfid = None if base_folder is None else base_folder.id
        res = self.gi.libraries.create_folder(
            library.id, name, description=description, base_folder_id=bfid,
            )
        folder_info = self.__get_dict('create_folder', res)
        return self.get_folder(library, folder_info['id'])

    def get_folder(self, library, f_id):
        """
        Retrieve the folder corresponding to the given id.

        :rtype: :class:`~bioblend.galaxy.objects.wrappers.Folder`
        :return: the folder corresponding to ``id_``
        """
        f_dict = self.gi.libraries.show_folder(library.id, f_id)
        return wrappers.Folder(f_dict, library.id)


class ObjDatasetClient(ObjClient):
    # default chunk size for reading remote data
    try:
        import resource
        _CHUNK_SIZE = resource.getpagesize()
    except StandardError:
        _CHUNK_SIZE = 4096

    def get_stream(self, dataset, chunk_size=_CHUNK_SIZE):
        """
        Open ``dataset`` for reading and return an iterator over its contents.

        :type dataset:
          :class:`~bioblend.galaxy.objects.wrappers.HistoryDatasetAssociation`
        :param dataset: the dataset to read from

        :type chunk_size: int
        :param chunk_size: read this amount of bytes at a time
        """
        hist_id = dataset.container_id
        base_url = self.gi._make_url(
            self.gi.histories, module_id=hist_id, contents=True
            )
        url = "%s/%s/display" % (base_url, dataset.id)
        get_options = {
            'verify': self.gi.verify,
            'params': {'key': self.gi.key},
            'stream': True,
            }
        r = requests.get(url, **get_options)
        r.raise_for_status()
        return r.iter_content(chunk_size)  # FIXME: client can't close r

    def peek(self, dataset, chunk_size=_CHUNK_SIZE):
        """
        Open ``dataset`` for reading and return the first chunk.

        See :meth:`.get_stream` for param info.
        """
        return self.get_stream(dataset, chunk_size=chunk_size).next()

    def download(self, dataset, outf, chunk_size=_CHUNK_SIZE):
        """
        Open ``dataset`` for reading and save its contents to ``outf``.

        :type outf: :obj:`file`
        :param outf: output file object

        See :meth:`.get_stream` for info on other params.
        """
        for chunk in self.get_stream(dataset, chunk_size=chunk_size):
            outf.write(chunk)

    def get_contents(self, dataset, chunk_size=_CHUNK_SIZE):
        """
        Open ``dataset`` for reading and return its **full** contents.

        See :meth:`.get_stream` for param info.
        """
        return ''.join(self.get_stream(dataset, chunk_size=chunk_size))

class ObjHistoryClient(ObjClient):

    def create(self, name=None):
        """
        Create a new Galaxy history, optionally setting its name.

        :rtype: :class:`~bioblend.galaxy.objects.wrappers.History`
        :return: the history just created
        """
        res = self.gi.histories.create_history(name=name)
        hist_info = self.__get_dict('create_history', res)
        return self.get(hist_info['id'])

    def get(self, id_):
        """
        Retrieve the history corresponding to the given id.

        :rtype: :class:`~bioblend.galaxy.objects.wrappers.History`
        :return: the history corresponding to ``id_``
        """
        return self.__get_container(id_, wrappers.History)

    def get_previews(self, name=None, deleted=False):
        """
        Get history previews for the user of this Galaxy instance.

        :type name: str
        :param name: return only histories with this name

        :type deleted: bool
        :param deleted: if :obj:`True`, return only deleted histories

        :rtype: list of
          :class:`~bioblend.galaxy.objects.wrappers.HistoryPreview`
        """
        dicts = self.gi.histories.get_histories(name=name, deleted=deleted)
        return [wrappers.HistoryPreview(_) for _ in dicts]

    def list(self, name=None):
        """
        Get histories owned by the user of this Galaxy instance.

        :type name: str
        :param name: return only histories with this name

        :rtype: list of :class:`~bioblend.galaxy.objects.wrappers.History`
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
            self.__error('update_history: failed to update %r' % (history.id,))
        return self.get(history.id)

    def delete(self, history, purge=False):
        """
        Delete the given history.

        :type purge: bool
        :param purge: if :obj:`True`, also purge the history (requires
          ``allow_user_dataset_purge = True`` to be set in Galaxy's
          configuration file ``universe_wsgi.ini``)
        """
        if not history.is_mapped:
            self.__error('history is not mapped to a Galaxy object')
        res = self.gi.histories.delete_history(history.id, purge=purge)
        if not isinstance(res, collections.Mapping):
            self.__error('delete_history: unexpected reply: %r' % (res,))
        history.unmap()

    #-- history contents --

    def import_dataset_into(self, history, lds):
        """
        Import a dataset into the history from a library.

        :type history: :class:`~bioblend.galaxy.objects.wrappers.History`
        :param history: target history

        :type lds: :class:`~bioblend.galaxy.objects.wrappers.LibraryDataset`
        :param lds: the library dataset to import

        :rtype:
          :class:`~bioblend.galaxy.objects.wrappers.HistoryDatasetAssociation`
        :return: the imported history dataset
        """
        if not history.is_mapped:
            self.__error('history is not mapped to a Galaxy object')
        if not isinstance(lds, wrappers.LibraryDataset):
            self.__error('lds is not a LibraryDataset', err_type=TypeError)
        # upload_dataset_from_library returns a dict with the unencoded id
        # to get the encoded id, we have to detect the new entry by diff
        old_ids = set(history.dataset_ids)
        res = self.gi.histories.upload_dataset_from_library(history.id, lds.id)
        if not isinstance(res, collections.Mapping):
            self.__error(
                'upload_dataset_from_library: unexpected reply: %r' % (res,)
                )
        history = self.get(history.id)  # refresh
        diff = set(history.dataset_ids) - old_ids
        if len(diff) != 1:
            self.__error('cannot retrieve hda id')
        return self.get_dataset(history, diff.pop())

    def get_dataset(self, src, ds_id):
        """
        Retrieve the history dataset corresponding to the given id.

        :rtype:
          :class:`~bioblend.galaxy.objects.wrappers.HistoryDatasetAssociation`
        :return: the history dataset corresponding to ``id_``
        """
        return self.__get_container_dataset(src, ds_id, wrappers.History)

class ObjWorkflowClient(ObjClient):
    # dataset states corresponding to a 'pending' condition
    _PENDING = set(["new", "upload", "queued", "running", "setting_metadata"])

    # default polling interval for output state monitoring
    _POLLING_INTERVAL = 10

    def import_one(self, src):
        """
        Imports a new workflow into Galaxy.

        :type src: :class:`~bioblend.galaxy.objects.wrappers.Workflow`
          or dict or str
        :param src: the workflow to import as a workflow object, or
          deserialized JSON (dictionary), or serialized JSON (unicode).

        :rtype: :class:`~bioblend.galaxy.objects.wrappers.Workflow`
        :return: the workflow just imported
        """
        if isinstance(src, wrappers.Workflow):
            if src.is_mapped:
                self.__error('workflow already imported')
            wf_dict = src.wrapped
        elif isinstance(src, collections.Mapping):
            wf_dict = src
        else:
            try:
                wf_dict = json.loads(src)
            except (TypeError, ValueError):
                self.__error('src not supported: %r' % (src,))
        wf_info = self.gi.workflows.import_workflow_json(wf_dict)
        return self.get(wf_info['id'])

    def get(self, id_):
        """
        Retrieve the workflow corresponding to the given id.

        :rtype: :class:`~bioblend.galaxy.objects.wrappers.Workflow`
        :return: the workflow corresponding to ``id_``
        """
        wf_dict = self.gi.workflows.export_workflow_json(id_)
        res = self.gi.workflows.show_workflow(id_)
        inputs = self.__get_dict('show_workflow', res)['inputs']
        return wrappers.Workflow(wf_dict, id=id_, inputs=inputs)

    # the 'deleted' option is not available for workflows
    def get_previews(self, name=None):
        """
        Get workflow previews for the user of this Galaxy instance.

        :type name: str
        :param name: return only workflows with this name

        :rtype: list of
          :class:`~bioblend.galaxy.objects.wrappers.WorkflowPreview`
        """
        dicts = self.gi.workflows.get_workflows(name=name)
        return [wrappers.WorkflowPreview(_) for _ in dicts]

    def list(self, name=None):
        """
        Get workflows owned by the user of this Galaxy instance.

        :type name: str
        :param name: return only workflows with this name

        :rtype: list of :class:`~bioblend.galaxy.objects.wrappers.Workflow`
        """
        dicts = self.gi.workflows.get_workflows(name=name)
        return [self.get(_['id']) for _ in dicts]

    def run_workflow(self, workflow, inputs, history, params=None,
                     import_inputs=False):
        """
        Run ``workflow`` with input datasets from the ``inputs`` sequence.

        :type workflow: :class:`~bioblend.galaxy.objects.wrappers.Workflow`
        :param workflow: the workflow that should be run

        :type inputs: :class:`~collections.Iterable` of
          :class:`~bioblend.galaxy.objects.wrappers.Dataset`
        :param inputs: input datasets for the workflow, which will be
          assigned to the workflow's input slots in the order they
          appear in ``inputs``; any extra items will be ignored.

        :type history:
          :class:`~bioblend.galaxy.objects.wrappers.History` or str
        :param history: either a valid history object (results will be
          stored there) or a string (a new history will be created with
          the given name).

        :type params: :class:`~collections.Mapping`
        :param params: an optional mapping of workflow tool indices to
          param dicts, such as::

            {1: {'a': 0}, 3: {'b': 1}}

          that sets ``a`` to 0 for ``workflow.tools[1]`` and ``b`` to 1
          for ``workflow.tools[3]``.

        :type import_inputs: bool
        :param import_inputs: If :obj:`True`, workflow inputs will be
          imported into the history; if :obj:`False`, only workflow
          outputs will be visible in the history.

        :rtype: list of str, str
        :return: list of output dataset ids, output history id

        .. warning::
          This is an asynchronous operation: when the method returns,
          the output datasets and history will most likely **not** be
          in their final state.  Use :meth:`.wait` if you want to block
          until they're ready.
        """
        if not workflow.is_mapped:
            self.__error('workflow is not mapped to a Galaxy object')
        if len(inputs) < len(workflow.inputs):
            self.__error('not enough inputs', err_type=ValueError)
        ds_map = workflow.get_input_map(inputs)
        params = self._build_params_payload(params, workflow)
        kwargs = {'import_inputs_to_history': import_inputs, 'params': params}
        if isinstance(history, wrappers.History):
            try:
                kwargs['history_id'] = history.id
            except AttributeError:
                self.__error('history does not have an id')
        elif not isinstance(history, basestring):
            self.__error(
                'history must be either a history wrapper or a string',
                err_type=TypeError,
                )
        else:
            kwargs['history_name'] = history
        res = self.gi.workflows.run_workflow(workflow.id, ds_map, **kwargs)
        res = self.__get_dict('run_workflow', res)
        # res structure: {'history': HIST_ID, 'outputs': [DS_ID, DS_ID, ...]}
        return res['outputs'], res['history']

    def wait(self, ds_ids, hist_id, polling_interval=_POLLING_INTERVAL):
        """
        Wait until all datasets are ready or one of them is in error.

        :type ds_ids: :class:`~collections.Iterable` of str
        :param ds_ids: dataset ids, which should belong to the history
          identified by ``hist_id`` (any that doesn't will be ignored)

        :type polling_interval: float
        :param polling_interval: polling interval in seconds

        .. warning::
          This is a blocking operation that can take a very long time.
          Also, note that this method does not return anything: if
          needed, the datasets and updated history must be retrieved
          explicitly.
        """
        self.log.info('waiting for datasets')
        while True:
            res = self.gi.histories.show_history(hist_id)
            hist_dict = self.__get_dict('show_history', res)
            ds_states = self._get_ds_states(hist_dict)
            pending = 0
            for id_ in ds_ids:
                state = ds_states.get(id_)
                self.log.info('%s: %s' % (id_, state))
                if state == 'error':
                    self.__error(self.__get_error_info(id_, hist_dict))
                if state in self._PENDING:
                    pending += 1
            if not pending:
                break
            time.sleep(polling_interval)

    def delete(self, workflow):
        """
        Delete the given workflow.

        .. warning::
          Deleting a workflow is irreversible - all of the data from
          the workflow will be permanently deleted.
        """
        if not workflow.is_mapped:
            self.__error('workflow is not mapped to a Galaxy object')
        res = self.gi.workflows.delete_workflow(workflow.id)
        if not isinstance(res, basestring):
            self.__error('delete_workflow: unexpected reply: %r' % (res,))
        workflow.unmap()

    def __get_error_info(self, ds_id, hist_dict):
        msg = ds_id
        try:
            # get history's dataset
            ds = self.__get_container_dataset(hist_dict, ds_id, wrappers.History)
            msg += ' (%s): ' % ds.name
            msg += ds.misc_info
        except StandardError:  # avoid 'error while generating an error report'
            msg += ': error'
        return msg

    @staticmethod
    def _get_ds_states(hist_dict):
        """
        Get a dataset_id-to-state mapping from the given history dict.
        """
        return dict(
            (id_, state)
            for state, ids in hist_dict['state_ids'].iteritems()
            for id_ in ids
            )

    @staticmethod
    def _build_params_payload(params, workflow):
        if params is None:
            return None
        payload = {}
        tools = workflow.tools()
        for i, pdict in params.iteritems():
            k, v = pdict.items()[0]
            payload[tools[i].tool_id] = {'param': k, 'value': v}
        return payload


