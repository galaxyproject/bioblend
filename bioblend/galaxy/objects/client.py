"""
Clients for interacting with specific Galaxy entity types.

Classes in this module should not be instantiated directly, but used
via their handles in :class:`~.galaxy_instance.GalaxyInstance`.
"""
import abc
import json
from collections.abc import (
    Mapping,
    Sequence,
)
from typing import List

import bioblend
from . import wrappers


class ObjClient(abc.ABC):

    def __init__(self, obj_gi):
        self.obj_gi = obj_gi
        self.gi = self.obj_gi.gi
        self.log = bioblend.log

    @abc.abstractmethod
    def get(self, id_) -> wrappers.Wrapper:
        """
        Retrieve the object corresponding to the given id.
        """
        pass

    @abc.abstractmethod
    def get_previews(self) -> list:
        """
        Get a list of object previews.

        Previews entity summaries provided by REST collection URIs, e.g.
        ``http://host:port/api/libraries``.  Being the most lightweight objects
        associated to the various entities, these are the ones that should be
        used to retrieve their basic info.

        :rtype: list
        :return: a list of object previews
        """
        pass

    @abc.abstractmethod
    def list(self) -> list:
        """
        Get a list of objects.

        This method first gets the entity summaries, then gets the complete
        description for each entity with an additional GET call, so may be slow.

        :rtype: list
        :return: a list of objects
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

    def _error(self, msg, err_type=RuntimeError):
        self.log.error(msg)
        raise err_type(msg)

    def _get_dict(self, meth_name, reply):
        if reply is None:
            self._error(f"{meth_name}: no reply")
        elif isinstance(reply, Mapping):
            return reply
        try:
            return reply[0]
        except (TypeError, IndexError):
            self._error(f'{meth_name}: unexpected reply: {reply!r}')


class ObjDatasetContainerClient(ObjClient):

    def _get_container(self, id_, ctype):
        show_fname = f"show_{ctype.__name__.lower()}"
        gi_client = getattr(self.gi, ctype.API_MODULE)
        show_f = getattr(gi_client, show_fname)
        res = show_f(id_)
        cdict = self._get_dict(show_fname, res)
        cdict['id'] = id_  # overwrite unencoded id
        c_infos = show_f(id_, contents=True)
        if not isinstance(c_infos, Sequence):
            self._error(f'{show_fname}: unexpected reply: {c_infos!r}')
        c_infos = [ctype.CONTENT_INFO_TYPE(_) for _ in c_infos]
        return ctype(cdict, content_infos=c_infos, gi=self.obj_gi)


class ObjLibraryClient(ObjDatasetContainerClient):
    """
    Interacts with Galaxy libraries.
    """

    def __init__(self, obj_gi):
        super().__init__(obj_gi)

    def create(self, name, description=None, synopsis=None):
        """
        Create a data library with the properties defined in the arguments.

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

    def list(self, name=None, deleted=False):
        """
        Get libraries owned by the user of this Galaxy instance.

        :type name: str
        :param name: return only libraries with this name
        :type deleted: bool
        :param deleted: if ``True``, return libraries that have been deleted

        :rtype: list of :class:`~.wrappers.Library`
        """
        dicts = self.gi.libraries.get_libraries(name=name, deleted=deleted)
        if not deleted:
            # return Library objects only for not-deleted libraries since Galaxy
            # does not filter them out and Galaxy release_14.08 and earlier
            # crashes when trying to get a deleted library
            return [self.get(_['id']) for _ in dicts if not _['deleted']]
        else:
            return [self.get(_['id']) for _ in dicts]

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
            if not isinstance(res, Mapping):
                self._error(f'delete_library: unexpected reply: {res!r}')


class ObjHistoryClient(ObjDatasetContainerClient):
    """
    Interacts with Galaxy histories.
    """

    def __init__(self, obj_gi):
        super().__init__(obj_gi)

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

    def list(self, name=None, deleted=False):
        """
        Get histories owned by the user of this Galaxy instance.

        :type name: str
        :param name: return only histories with this name
        :type deleted: bool
        :param deleted: if ``True``, return histories that have been deleted

        :rtype: list of :class:`~.wrappers.History`
        """
        dicts = self.gi.histories.get_histories(name=name, deleted=deleted)
        return [self.get(_['id']) for _ in dicts]

    def delete(self, id_=None, name=None, purge=False):
        """
        Delete the history with the given id or name.

        Note that the same name can map to multiple histories.

        :type purge: bool
        :param purge: if ``True``, also purge (permanently delete) the history

        .. note::
          For the purge option to work, the Galaxy instance must have the
          ``allow_user_dataset_purge`` option set to ``true`` in the
          ``config/galaxy.yml`` configuration file.
        """
        for id_ in self._select_ids(id_=id_, name=name):
            res = self.gi.histories.delete_history(id_, purge=purge)
            if not isinstance(res, Mapping):
                self._error(f'delete_history: unexpected reply: {res!r}')


class ObjWorkflowClient(ObjClient):
    """
    Interacts with Galaxy workflows.
    """

    def import_new(self, src, publish=False):
        """
        Imports a new workflow into Galaxy.

        :type src: dict or str
        :param src: deserialized (dictionary) or serialized (str) JSON
          dump of the workflow (this is normally obtained by exporting
          a workflow from Galaxy).

        :type publish: bool
        :param publish:  if ``True`` the uploaded workflow will be published;
                         otherwise it will be visible only by the user which uploads it (default).

        :rtype: :class:`~.wrappers.Workflow`
        :return: the workflow just imported
        """
        if isinstance(src, Mapping):
            wf_dict = src
        else:
            try:
                wf_dict = json.loads(src)
            except (TypeError, ValueError):
                self._error(f'src not supported: {src!r}')
        wf_info = self.gi.workflows.import_workflow_dict(wf_dict, publish)
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
        dicts = self.gi.workflows.get_workflows(name=name, published=published)
        return [wrappers.WorkflowPreview(_, gi=self.obj_gi) for _ in dicts]

    # the 'deleted' option is not available for workflows
    def list(self, name=None, published=False):
        """
        Get workflows owned by the user of this Galaxy instance.

        :type name: str
        :param name: return only workflows with this name
        :type published: bool
        :param published: if ``True``, return also published workflows

        :rtype: list of :class:`~.wrappers.Workflow`
        """
        dicts = self.gi.workflows.get_workflows(name=name, published=published)
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
            if not isinstance(res, str):
                self._error(f"delete_workflow: unexpected reply: {res!r}")


class ObjInvocationClient(ObjClient):
    """
    Interacts with Galaxy Invocations.
    """
    def get(self, id_) -> wrappers.Invocation:
        """
        Get an invocation by ID.

        :rtype: Invocation
        :param: invocation object
        """
        inv_dict = self.gi.invocations.show_invocation(id_)
        return wrappers.Invocation(inv_dict, self.obj_gi)

    def get_previews(self) -> List[wrappers.InvocationPreview]:
        """
        Get previews of all invocations.

        :rtype: list of InvocationPreview
        :param: previews of invocations
        """
        inv_list = self.gi.invocations.get_invocations()
        return [wrappers.InvocationPreview(inv_dict, self.obj_gi) for inv_dict in inv_list]

    def list(
        self,
        workflow=None,
        history=None,
        include_terminal=True,
        limit=None
    ) -> List[wrappers.Invocation]:
        """
        Get full listing of workflow invocations, or select a subset
        by specifying optional arguments for filtering (e.g. a workflow).

        :type workflow: wrappers.Workflow
        :param workflow: Include only invocations associated with
          this workflow

        :type history: str
        :param history: Include only invocations associated with
          this history

        :param include_terminal: bool
        :param: Whether to include invocations in terminal states

        :type limit: int
        :param limit: Maximum number of invocations to return - if specified,
          the most recent invocations will be returned.

        :rtype: list of Invocation
        :param: invocation objects
        """
        inv_dict_list = self.gi.invocations.get_invocations(
            workflow_id=workflow.id if workflow else None,
            history_id=history.id if history else None,
            include_terminal=include_terminal,
            limit=limit,
            view='element',
            step_details=True
        )
        return [wrappers.Invocation(inv_dict, self.obj_gi) for inv_dict in inv_dict_list]


class ObjToolClient(ObjClient):
    """
    Interacts with Galaxy tools.
    """

    def get(self, id_, io_details=False, link_details=False):
        """
        Retrieve the tool corresponding to the given id.

        :type io_details: bool
        :param io_details: if True, get also input and output details

        :type link_details: bool
        :param link_details: if True, get also link details

        :rtype: :class:`~.wrappers.Tool`
        :return: the tool corresponding to ``id_``
        """
        res = self.gi.tools.show_tool(id_, io_details=io_details,
                                      link_details=link_details)
        tool_dict = self._get_dict('show_tool', res)
        return wrappers.Tool(tool_dict, gi=self.obj_gi)

    def get_previews(self, name=None, trackster=None):
        """
        Get the list of tools installed on the Galaxy instance.

        :type name: str
        :param name: return only tools with this name

        :type trackster: bool
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

        :type trackster: bool
        :param trackster: if True, only tools that are compatible with
          Trackster are returned

        :rtype: list of :class:`~.wrappers.Tool`
        """
        # dicts = self.gi.tools.get_tools(name=name, trackster=trackster)
        # return [self.get(_['id']) for _ in dicts]
        # As of 2015/04/15, GET /api/tools returns also data manager tools for
        # non-admin users, see
        # https://trello.com/c/jyl0cvFP/2633-api-tool-list-filtering-doesn-t-filter-data-managers-for-non-admins
        # Trying to get() a data manager tool would then return a 404 Not Found
        # error.
        # Moreover, the dicts returned by gi.tools.get_tools() are richer than
        # those returned by get(), so make this an alias for get_previews().
        return self.get_previews(name, trackster)


class ObjJobClient(ObjClient):
    """
    Interacts with Galaxy jobs.
    """

    def get(self, id_, full_details=False):
        """
        Retrieve the job corresponding to the given id.

        :type full_details: bool
        :param full_details: if ``True``, return the complete list of details
          for the given job.

        :rtype: :class:`~.wrappers.Job`
        :return: the job corresponding to ``id_``
        """
        res = self.gi.jobs.show_job(id_, full_details)
        job_dict = self._get_dict('job_tool', res)
        return wrappers.Job(job_dict, gi=self.obj_gi)

    def get_previews(self):
        dicts = self.gi.jobs.get_jobs()
        return [wrappers.JobPreview(_, gi=self.obj_gi) for _ in dicts]

    def list(self):
        """
        Get the list of jobs of the current user.

        :rtype: list of :class:`~.wrappers.Job`
        """
        dicts = self.gi.jobs.get_jobs()
        return [self.get(_['id']) for _ in dicts]
