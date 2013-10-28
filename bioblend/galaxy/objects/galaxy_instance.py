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

    def create_library(self, name, description=None, synopsis=None):
        res = self.gi.libraries.create_library(name, description, synopsis)
        if isinstance(res, collections.Mapping):
            lib_info = res
        elif res is None:
            self.__error('create_library: no reply')
        else:
            # older versions of Galaxy returned a list containing a dictionary
            try:
                lib_info = res[0]
            except (TypeError, IndexError):
                self.__error('create_library: unexpected reply: %r' % (res,))
        return self.get_library(lib_info['id'])

    def get_library(self, id):
        lib_dict = self.gi.libraries.show_library(id)
        return wrappers.Library(lib_dict, id=id)

    def get_libraries(self):
        lib_infos = self.gi.libraries.get_libraries()
        return [self.get_library(li['id']) for li in lib_infos]

    def delete_library(self, library):
        if library.id is None:
            self.__error('delete_library: library does not have an id')
        res = self.gi.libraries.delete_library(library.id)
        if not isinstance(res, collections.Mapping):
            self.__error('delete_library: unexpected reply: %r' % (res,))
        library.touch()

    def create_folder(self, library, name, description=None, base_folder=None):
        folder_infos = self.gi.libraries.create_folder(
            library.id,
            name,
            description=description,
            base_folder_id=base_folder.id
            )
        # for unknown reasons, create_folder returns a list
        return wrappers.Folder(folder_infos[0], library)

    def create_history(self, name=None):
        hist_info = self.gi.histories.create_history(name=name)
        if not isinstance(hist_info, collections.Mapping):
            self.__error('create_history: unexpected reply: %r' % (hist_info,))
        return self.get_history(hist_info['id'])

    def get_history(self, id):
        hist_dict = self.gi.histories.show_history(id)
        if not isinstance(hist_dict, collections.Mapping):
            self.__error('get_history: unexpected reply: %r' % (hist_dict,))
        contents = self.gi.histories.show_history(id, contents=True)
        if not isinstance(contents, collections.Sequence):
            self.__error('get_history: unexpected reply: %r' % (contents,))
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
            self.__error('delete_history: history does not have an id')
        res = self.gi.histories.delete_history(history.id, purge=purge)
        if not isinstance(res, collections.Mapping):
            self.__error('delete_history: unexpected reply: %r' % (res,))
        history.touch()

    def import_workflow(self, workflow):
        if workflow.id is not None:
            self.__error('import_workflow: workflow already has an id')
        wf_info = self.gi.workflows.import_workflow_json(workflow.core.wrapped)
        return self.get_workflow(wf_info['id'])

    def get_workflow(self, id):
        wf_dict = self.gi.workflows.export_workflow_json(id)
        res = self.gi.workflows.show_workflow(id)
        if not isinstance(res, collections.Mapping):
            self.__error('get_workflow: unexpected reply: "%s"' % (res,))
        links = res['inputs']
        return wrappers.Workflow(wf_dict, id=id, links=links)

    def get_workflows(self):
        wf_infos = self.gi.workflows.get_workflows()
        return [self.get_workflow(wi['id']) for wi in wf_infos]

    def delete_workflow(self, workflow):
        if workflow.id is None:
            self.__error('delete_workflow: workflow does not have an id')
        res = self.gi.workflows.delete_workflow(workflow.id)
        if not isinstance(res, basestring):
            self.__error('delete_workflow: unexpected reply: %r' % (res,))
        workflow.touch()
