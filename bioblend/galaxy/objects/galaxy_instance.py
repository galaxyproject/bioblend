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
            self.__error("create_library: no reply")
        else:
            # older versions of Galaxy returned a list containing a dictionary
            try:
                lib_info = res[0]
            except (TypeError, IndexError):
                self.__error("create_library: unexpected reply: %r" % (res,))
        return self.get_library(lib_info['id'])

    def get_library(self, id):
        lib_dict = self.gi.libraries.show_library(id)
        return wrappers.Library(lib_dict, id=id)

    def get_libraries(self):
        lib_infos = self.gi.libraries.get_libraries()
        return [self.get_library(li['id']) for li in lib_infos]

    def delete_library(self, library):
        if library.id is None:
            self.__error('library does not have an id')
        dlib = wrappers.Library(self.gi.libraries.delete_library(library.id))
        library.touch()
        return dlib

    def create_folder(self, library, name, description=None, base_folder=None):
        folder_infos = self.gi.libraries.create_folder(
            library.id,
            name,
            description=description,
            base_folder_id=base_folder.id
            )
        # for unknown reasons, create_folder returns a list
        return wrappers.Folder(folder_infos[0], library)

    def get_history(self, id):
        hist_dict = self.gi.histories.show_history(id)
        contents = self.gi.histories.show_history(id, contents=True)
        hdas = [wrappers.HistoryDatasetAssociation(
            self.gi.histories.show_dataset(id, c['id'])
            ) for c in contents]
        return wrappers.History(hist_dict, hdas)

    def get_histories(self):
        hist_infos = self.gi.histories.get_histories()
        return [self.get_history(hi['id']) for hi in hist_infos]

    def update_history(self, history, name=None, annotation=None):
        res = self.gi.histories.update_history(
            history.id, name=name, annotation=annotation
            )
        if res != httplib.OK:
            self.__error('failed to update history "%s"' % history.id)
        return self.get_history(history.id)

    def import_workflow(self, workflow):
        if workflow.id is not None:
            self.__error('workflow already has an id')
        wf_info = self.gi.workflows.import_workflow_json(workflow.core.wrapped)
        return self.get_workflow(wf_info['id'])

    def get_workflow(self, id):
        wf_dict = self.gi.workflows.export_workflow_json(id)
        links = self.gi.workflows.show_workflow(id)['inputs']
        return wrappers.Workflow(wf_dict, id=id, links=links)

    def get_workflows(self):
        wf_infos = self.gi.workflows.get_workflows()
        return [self.get_workflow(wi['id']) for wi in wf_infos]

    def delete_workflow(self, workflow):
        if workflow.id is None:
            self.__error('workflow does not have an id')
        msg = self.gi.workflows.delete_workflow(workflow.id)
        workflow.touch()
        return msg
