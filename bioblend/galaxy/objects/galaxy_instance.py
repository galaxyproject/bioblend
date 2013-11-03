"""
A representation of a Galaxy instance based on oo wrappers.
"""
import httplib, collections, json

import bioblend
import bioblend.galaxy

import wrappers


class GalaxyInstance(object):

    def __init__(self, url, api_key):
        self.gi = bioblend.galaxy.GalaxyInstance(url, api_key)
        self.log = bioblend.log

    #-- library --

    def create_library(self, name, description=None, synopsis=None):
        res = self.gi.libraries.create_library(name, description, synopsis)
        lib_info = self.__get_dict('create_library', res)
        return self.get_library(lib_info['id'])

    def get_library(self, id):
        return self.__get_container(id, wrappers.Library)

    def get_libraries(self):
        lib_infos = self.gi.libraries.get_libraries()
        return [self.get_library(li['id']) for li in lib_infos]

    def delete_library(self, library):
        if library.id is None:
            self.__error('library does not have an id')
        res = self.gi.libraries.delete_library(library.id)
        if not isinstance(res, collections.Mapping):
            self.__error('delete_library: unexpected reply: %r' % (res,))
        library.touch()

    #-- library contents --

    def upload_data(self, library, data, folder=None, **kwargs):
        fid = self.__pre_upload(library, folder)
        res = self.gi.libraries.upload_file_contents(
            library.id, data, folder_id=fid, **kwargs
            )
        return self.__post_upload(library, 'upload_file_contents', res)

    def upload_from_url(self, library, url, folder=None, **kwargs):
        fid = self.__pre_upload(library, folder)
        res = self.gi.libraries.upload_file_from_url(
            library.id, url, fid, **kwargs
            )
        return self.__post_upload(library, 'upload_file_from_url', res)

    def upload_from_local(self, library, path, folder=None, **kwargs):
        fid = self.__pre_upload(library, folder)
        res = self.gi.libraries.upload_file_from_local_path(
            library.id, path, fid, **kwargs
            )
        return self.__post_upload(library, 'upload_file_from_local_path', res)

    def upload_from_galaxy_fs(self, library, paths, folder=None, **kwargs):
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
        return [self.get_library_dataset(library, ds_info['id'])
                for ds_info in res]

    def get_library_dataset(self, src, ds_id):
        return self.__get_container_dataset(src, ds_id, wrappers.Library)

    def create_folder(self, library, name, description=None, base_folder=None):
        bfid = None if base_folder is None else base_folder.id
        res = self.gi.libraries.create_folder(
            library.id, name, description=description, base_folder_id=bfid,
            )
        folder_info = self.__get_dict('create_folder', res)
        return self.get_folder(library, folder_info['id'])

    def get_folder(self, library, f_id):
        f_dict = self.gi.libraries.show_folder(library.id, f_id)
        return wrappers.Folder(f_dict, library)

    #-- history --

    def create_history(self, name=None):
        res = self.gi.histories.create_history(name=name)
        hist_info = self.__get_dict('create_history', res)
        return self.get_history(hist_info['id'])

    def get_history(self, id):
        return self.__get_container(id, wrappers.History)

    def get_histories(self):
        hist_infos = self.gi.histories.get_histories()
        return [self.get_history(hi['id']) for hi in hist_infos]

    def update_history(self, history, name=None, annotation=None):
        res = self.gi.histories.update_history(
            history.id, name=name, annotation=annotation
            )
        if res != httplib.OK:
            self.__error('update_history: failed to update %r' % (history.id,))
        return self.get_history(history.id)

    def delete_history(self, history, purge=False):
        if history.id is None:
            self.__error('history does not have an id')
        res = self.gi.histories.delete_history(history.id, purge=purge)
        if not isinstance(res, collections.Mapping):
            self.__error('delete_history: unexpected reply: %r' % (res,))
        history.touch()

    #-- history contents --

    def import_dataset_to_history(self, history, lds):
        if history.id is None:
            self.__error('history does not have an id')
        if not isinstance(lds, wrappers.LibraryDataset):
            self.__error('lds is not a LibraryDataset', err_type=TypeError)
        # upload_dataset_from_library returns a dict with the unencoded id
        # to get the encoded id, we have to detect the new entry by diff
        dataset_ids = lambda h: set(_.id for _ in h.datasets)
        old_ids = dataset_ids(history)
        res = self.gi.histories.upload_dataset_from_library(history.id, lds.id)
        if not isinstance(res, collections.Mapping):
            self.__error(
                'upload_dataset_from_library: unexpected reply: %r' % (res,)
                )
        history = self.get_history(history.id)  # refresh
        diff = dataset_ids(history) - old_ids
        if len(diff) != 1:
            self.__error('cannot retrieve hda id')
        return self.get_history_dataset(history, diff.pop())

    def get_history_dataset(self, src, ds_id):
        return self.__get_container_dataset(src, ds_id, wrappers.History)

    #-- workflow --

    def import_workflow(self, src):
        if isinstance(src, wrappers.Workflow):
            if src.id is not None:
                self.__error('workflow already has an id: %r' % (src.id,))
            wf_dict = src.core.wrapped
        elif isinstance(src, collections.Mapping):
            wf_dict = src
        else:
            try:
                wf_dict = json.loads(src)
            except (TypeError, ValueError):
                self.__error('src not supported: %r' % (src,))
        wf_info = self.gi.workflows.import_workflow_json(wf_dict)
        return self.get_workflow(wf_info['id'])

    def get_workflow(self, id):
        wf_dict = self.gi.workflows.export_workflow_json(id)
        res = self.gi.workflows.show_workflow(id)
        links = self.__get_dict('show_workflow', res)['inputs']
        return wrappers.Workflow(wf_dict, id=id, links=links)

    def get_workflows(self):
        wf_infos = self.gi.workflows.get_workflows()
        return [self.get_workflow(wi['id']) for wi in wf_infos]

    def delete_workflow(self, workflow):
        if workflow.id is None:
            self.__error('workflow does not have an id')
        res = self.gi.workflows.delete_workflow(workflow.id)
        if not isinstance(res, basestring):
            self.__error('delete_workflow: unexpected reply: %r' % (res,))
        workflow.touch()

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

    def __get_container(self, id, ctype):
        show_fname = 'show_%s' % ctype.__name__.lower()
        gi_client = getattr(self.gi, ctype.API_MODULE)
        show_f = getattr(gi_client, show_fname)
        res = show_f(id)
        cdict = self.__get_dict(show_fname, res)
        cdict['id'] = id  # overwrite unencoded id
        ds_infos = show_f(id, contents=True)
        if not isinstance(ds_infos, collections.Sequence):
            self.__error('%s: unexpected reply: %r' % (show_fname, ds_infos))
        dss = [self.__get_container_dataset(cdict, di['id'], ctype=ctype)
               for di in ds_infos if di['type'] != 'folder']
        return ctype(cdict, id=id, datasets=dss)

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
        return ctype.DS_TYPE(ds_dict)

    def __pre_upload(self, library, folder):
        if library.id is None:
            self.__error('library does not have an id')
        return None if folder is None else folder.id

    def __post_upload(self, library, meth_name, reply):
        ds_info = self.__get_dict(meth_name, reply)
        return self.get_library_dataset(library, ds_info['id'])
