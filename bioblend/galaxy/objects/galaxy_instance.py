"""
A representation of a Galaxy instance based on oo wrappers.
"""
import httplib, collections

import bioblend
import bioblend.galaxy

import wrappers


class GalaxyInstance(object):

    def __init__(self, url, api_key):
        self.gi = bioblend.galaxy.GalaxyInstance(url, api_key)
        self.log = bioblend.log

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

    def create_library(self, name, description=None, synopsis=None):
        res = self.gi.libraries.create_library(name, description, synopsis)
        lib_info = self.__get_dict("create_library", res)
        return self.get_library(lib_info['id'])

    def get_library(self, id):
        lib_dict = self.gi.libraries.show_library(id)
        return wrappers.Library(lib_dict, id=id)

    def get_libraries(self):
        lib_infos = self.gi.libraries.get_libraries()
        return [self.get_library(li['id']) for li in lib_infos]

    def upload_file_contents(
        self, library, data, folder=None, file_type='auto', dbkey='?'
        ):
        if library.id is None:
            self.__error('library does not have an id')
        fid = None if folder is None else folder.id
        res = self.gi.libraries.upload_file_contents(
            library.id, data, folder_id=fid, file_type=file_type, dbkey=dbkey
            )
        ds_info = self.__get_dict("upload_file_contents", res)
        return self.get_library_dataset(library, ds_info['id'])

    def get_library_dataset(self, library, ds_id):
        ds_dict = self.gi.libraries.show_dataset(library.id, ds_id)
        return wrappers.LibraryDataset(ds_dict)

    def delete_library(self, library):
        if library.id is None:
            self.__error('library does not have an id')
        res = self.gi.libraries.delete_library(library.id)
        if not isinstance(res, collections.Mapping):
            self.__error('delete_library: unexpected reply: %r' % (res,))
        library.touch()

    def create_folder(self, library, name, description=None, base_folder=None):
        bfid = None if base_folder is None else base_folder.id
        res = self.gi.libraries.create_folder(
            library.id, name, description=description, base_folder_id=bfid,
            )
        folder_info = self.__get_dict("create_folder", res)
        return self.get_folder(library, folder_info['id'])

    def get_folder(self, library, f_id):
        f_dict = self.gi.libraries.show_folder(library.id, f_id)
        return wrappers.Folder(f_dict, library)

    def create_history(self, name=None):
        res = self.gi.histories.create_history(name=name)
        hist_info = self.__get_dict("create_history", res)
        return self.get_history(hist_info['id'])

    def get_history(self, id):
        res = self.gi.histories.show_history(id)
        hist_dict = self.__get_dict("show_history", res)
        contents = self.gi.histories.show_history(id, contents=True)
        if not isinstance(contents, collections.Sequence):
            self.__error('show_history: unexpected reply: %r' % (contents,))
        hdas = [wrappers.HistoryDatasetAssociation(
            self.gi.histories.show_dataset(id, c['id'])
            ) for c in contents]
        return wrappers.History(hist_dict, id=hist_dict['id'], datasets=hdas)

    def get_histories(self):
        hist_infos = self.gi.histories.get_histories()
        return [self.get_history(hi['id']) for hi in hist_infos]

    def update_history(self, history, name=None, annotation=None):
        res = self.gi.histories.update_history(
            history.id, name=name, annotation=annotation
            )
        if res != httplib.OK:
            self.__error('update_history: failed to update "%s"' % history.id)
        return self.get_history(history.id)

    def delete_history(self, history, purge=False):
        if history.id is None:
            self.__error('history does not have an id')
        res = self.gi.histories.delete_history(history.id, purge=purge)
        if not isinstance(res, collections.Mapping):
            self.__error('delete_history: unexpected reply: %r' % (res,))
        history.touch()

    def import_workflow(self, workflow):
        if workflow.id is not None:
            self.__error('workflow already has an id')
        wf_info = self.gi.workflows.import_workflow_json(workflow.core.wrapped)
        return self.get_workflow(wf_info['id'])

    def get_workflow(self, id):
        wf_dict = self.gi.workflows.export_workflow_json(id)
        res = self.gi.workflows.show_workflow(id)
        links = self.__get_dict("show_workflow", res)['inputs']
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
