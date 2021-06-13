# pylint: disable=W0622,E1101

"""
A basic object-oriented interface for Galaxy entities.
"""

import abc
import json
from collections.abc import (
    Iterable,
    Mapping,
    Sequence,
)
from typing import Tuple

import bioblend
from bioblend.util import abstractclass


__all__ = (
    'Wrapper',
    'Step',
    'Workflow',
    'LibraryContentInfo',
    'HistoryContentInfo',
    'DatasetContainer',
    'History',
    'Library',
    'Folder',
    'Dataset',
    'HistoryDatasetAssociation',
    'DatasetCollection',
    'HistoryDatasetCollectionAssociation',
    'LibraryDatasetDatasetAssociation',
    'LibraryDataset',
    'Tool',
    'Job',
    'LibraryPreview',
    'HistoryPreview',
    'WorkflowPreview',
)


@abstractclass
class Wrapper:
    """
    Abstract base class for Galaxy entity wrappers.

    Wrapper instances wrap deserialized JSON dictionaries such as the
    ones obtained by the Galaxy web API, converting key-based access to
    attribute-based access (e.g., ``library['name'] -> library.name``).

    Dict keys that are converted to attributes are listed in the
    ``BASE_ATTRS`` class variable: this is the 'stable' interface.
    Note that the wrapped dictionary is accessible via the ``wrapped``
    attribute.
    """
    BASE_ATTRS: Tuple[str, ...] = ('id', )

    def __init__(self, wrapped, parent=None, gi=None):
        """
        :type wrapped: dict
        :param wrapped: JSON-serializable dictionary

        :type parent: :class:`Wrapper`
        :param parent: the parent of this wrapper

        :type gi: :class:`GalaxyInstance`
        :param gi: the GalaxyInstance through which we can access this wrapper
        """
        if not isinstance(wrapped, Mapping):
            raise TypeError('wrapped object must be a mapping type')
        # loads(dumps(x)) is a bit faster than deepcopy and allows type checks
        try:
            dumped = json.dumps(wrapped)
        except (TypeError, ValueError):
            raise ValueError('wrapped object must be JSON-serializable')
        object.__setattr__(self, 'wrapped', json.loads(dumped))
        for k in self.BASE_ATTRS:
            object.__setattr__(self, k, self.wrapped.get(k))
        object.__setattr__(self, '_cached_parent', parent)
        object.__setattr__(self, 'is_modified', False)
        object.__setattr__(self, 'gi', gi)

    @property
    def parent(self):
        """
        The parent of this wrapper.
        """
        return self._cached_parent

    @property
    def is_mapped(self):
        """
        ``True`` if this wrapper is mapped to an actual Galaxy entity.
        """
        return self.id is not None

    def unmap(self):
        """
        Disconnect this wrapper from Galaxy.
        """
        object.__setattr__(self, 'id', None)

    def clone(self):
        """
        Return an independent copy of this wrapper.
        """
        return self.__class__(self.wrapped)

    def touch(self):
        """
        Mark this wrapper as having been modified since its creation.
        """
        object.__setattr__(self, 'is_modified', True)
        if self.parent:
            self.parent.touch()

    def to_json(self):
        """
        Return a JSON dump of this wrapper.
        """
        return json.dumps(self.wrapped)

    @classmethod
    def from_json(cls, jdef):
        """
        Build a new wrapper from a JSON dump.
        """
        return cls(json.loads(jdef))

    # FIXME: things like self.x[0] = 'y' do NOT call self.__setattr__
    def __setattr__(self, name, value):
        if name not in self.wrapped:
            raise AttributeError("can't set attribute")
        else:
            self.wrapped[name] = value
            object.__setattr__(self, name, value)
            self.touch()

    def __repr__(self):
        return f"{self.__class__.__name__}({self.wrapped!r})"


class Step(Wrapper):
    """
    Workflow step.

    Steps are the main building blocks of a Galaxy workflow. A step can be: an
    input (type ``data_collection_input``, ``data_input`` or
    ``parameter_input``), a computational tool (type ``tool``), a subworkflow
    (type ``subworkflow``) or a pause (type ``pause``).
    """
    BASE_ATTRS = Wrapper.BASE_ATTRS + (
        'input_steps',
        'name',
        'tool_id',
        'tool_inputs',
        'tool_version',
        'type',
    )

    def __init__(self, step_dict, parent):
        super().__init__(step_dict, parent=parent, gi=parent.gi)
        try:
            stype = step_dict['type']
        except KeyError:
            raise ValueError('not a step dict')
        if stype not in {'data_collection_input', 'data_input', 'parameter_input', 'pause', 'subworkflow', 'tool'}:
            raise ValueError(f"Unknown step type: {stype!r}")


class InvocationStep(Wrapper):
    """
    Invocation step.
    """
    BASE_ATTRS = Wrapper.BASE_ATTRS + (
        'action',
        'job_id',
        'order_index',
        'state',
        'update_time',
        'workflow_step_id',
        'workflow_step_label',
        'workflow_step_uuid',
    )


class Workflow(Wrapper):
    """
    Workflows represent ordered sequences of computations on Galaxy.

    A workflow defines a sequence of steps that produce one or more
    results from an input dataset.
    """
    BASE_ATTRS = Wrapper.BASE_ATTRS + (
        'deleted',
        'inputs',
        'latest_workflow_uuid',
        'name',
        'owner',
        'published',
        'steps',
        'tags',
    )
    POLLING_INTERVAL = 10  # for output state monitoring

    def __init__(self, wf_dict, gi=None):
        super().__init__(wf_dict, gi=gi)
        missing_ids = []
        if gi:
            tools_list_by_id = [t.id for t in gi.tools.get_previews()]
        else:
            tools_list_by_id = []
        tool_labels_to_ids = {}
        for k, v in self.steps.items():
            # convert step ids to str for consistency with outer keys
            v['id'] = str(v['id'])
            for i in v['input_steps'].values():
                i['source_step'] = str(i['source_step'])
            step = Step(v, self)
            self.steps[k] = step
            if step.type == 'tool':
                if not step.tool_inputs or step.tool_id not in tools_list_by_id:
                    missing_ids.append(k)
                tool_labels_to_ids.setdefault(step.tool_id, set()).add(step.id)
        input_labels_to_ids = {}
        for id_, d in self.inputs.items():
            input_labels_to_ids.setdefault(d['label'], set()).add(id_)
        object.__setattr__(self, 'input_labels_to_ids', input_labels_to_ids)
        object.__setattr__(self, 'tool_labels_to_ids', tool_labels_to_ids)
        dag, inv_dag = self._get_dag()
        heads, tails = set(dag), set(inv_dag)
        object.__setattr__(self, 'dag', dag)
        object.__setattr__(self, 'inv_dag', inv_dag)
        object.__setattr__(self, 'source_ids', heads - tails)
        assert set(self.inputs) == self.data_collection_input_ids | self.data_input_ids | self.parameter_input_ids, \
            f"inputs is {self.inputs!r}, while data_collection_input_ids is {self.data_collection_input_ids!r}, data_input_ids is {self.data_input_ids!r} and parameter_input_ids is {self.parameter_input_ids!r}"
        object.__setattr__(self, 'sink_ids', tails - heads)
        object.__setattr__(self, 'missing_ids', missing_ids)

    def _get_dag(self):
        """
        Return the workflow's DAG.

        For convenience, this method computes a 'direct' (step =>
        successors) and an 'inverse' (step => predecessors)
        representation of the same DAG.

        For instance, a workflow with a single tool *c*, two inputs
        *a, b* and three outputs *d, e, f* is represented by (direct)::

          {'a': {'c'}, 'b': {'c'}, 'c': {'d', 'e', 'f'}}

        and by (inverse)::

          {'c': {'a', 'b'}, 'd': {'c'}, 'e': {'c'}, 'f': {'c'}}
        """
        dag, inv_dag = {}, {}
        for s in self.steps.values():
            for i in s.input_steps.values():
                head, tail = i['source_step'], s.id
                dag.setdefault(head, set()).add(tail)
                inv_dag.setdefault(tail, set()).add(head)
        return dag, inv_dag

    def sorted_step_ids(self):
        """
        Return a topological sort of the workflow's DAG.
        """
        ids = []
        source_ids = self.source_ids.copy()
        inv_dag = {k: v.copy() for k, v in self.inv_dag.items()}
        while source_ids:
            head = source_ids.pop()
            ids.append(head)
            for tail in self.dag.get(head, []):
                incoming = inv_dag[tail]
                incoming.remove(head)
                if not incoming:
                    source_ids.add(tail)
        return ids

    @property
    def data_input_ids(self):
        """
        Return the ids of data input steps for this workflow.
        """
        return {id_ for id_, s in self.steps.items() if s.type == 'data_input'}

    @property
    def data_collection_input_ids(self):
        """
        Return the ids of data collection input steps for this workflow.
        """
        return {id_ for id_, s in self.steps.items() if s.type == 'data_collection_input'}

    @property
    def parameter_input_ids(self):
        """
        Return the ids of parameter input steps for this workflow.
        """
        return {id_ for id_, s in self.steps.items() if s.type == 'parameter_input'}

    @property
    def tool_ids(self):
        """
        Return the ids of tool steps for this workflow.
        """
        return {id_ for id_, s in self.steps.items() if s.type == 'tool'}

    @property
    def input_labels(self):
        """
        Return the labels of this workflow's input steps.
        """
        return set(self.input_labels_to_ids)

    @property
    def is_runnable(self):
        """
        Return True if the workflow can be run on Galaxy.

        A workflow is considered runnable on a Galaxy instance if all
        of the tools it uses are installed in that instance.
        """
        return not self.missing_ids

    def convert_input_map(self, input_map):
        """
        Convert ``input_map`` to the format required by the Galaxy web API.

        :type input_map: dict
        :param input_map: a mapping from input labels to datasets

        :rtype: dict
        :return: a mapping from input slot ids to dataset ids in the
          format required by the Galaxy web API.
        """
        m = {}
        for label, slot_ids in self.input_labels_to_ids.items():
            datasets = input_map.get(label, [])
            if not isinstance(datasets, Iterable):
                datasets = [datasets]
            if len(datasets) < len(slot_ids):
                raise RuntimeError(f'not enough datasets for "{label}"')
            for id_, ds in zip(slot_ids, datasets):
                m[id_] = {'id': ds.id, 'src': ds.SRC}
        return m

    def preview(self):
        getf = self.gi.workflows.get_previews
        try:
            p = [_ for _ in getf(published=True) if _.id == self.id][0]
        except IndexError:
            raise ValueError(f"no object for id {self.id}")
        return p

    def run(self, input_map=None, history='', params=None, import_inputs=False,
            replacement_params=None, wait=False,
            polling_interval=POLLING_INTERVAL, break_on_error=True):
        """
        Run the workflow in the current Galaxy instance.

        .. deprecated:: 0.16.0
           Use :meth:`invoke` instead.

        :type input_map: dict
        :param input_map: a mapping from workflow input labels to
          datasets, e.g.: ``dict(zip(workflow.input_labels,
          library.get_datasets()))``

        :type history: :class:`History` or str
        :param history: either a valid history object (results will be
          stored there) or a string (a new history will be created with
          the given name).

        :type params: dict
        :param params: a mapping of non-datasets tool parameters (see below)

        :type import_inputs: bool
        :param import_inputs: If ``True``, workflow inputs will be imported into
          the history; if ``False``, only workflow outputs will be visible in
          the history.

        :type replacement_params: dict
        :param replacement_params: pattern-based replacements for
          post-job actions (see the docs for
          :meth:`~bioblend.galaxy.workflows.WorkflowClient.invoke_workflow`)

        :type wait: bool
        :param wait: whether to wait while the returned datasets are
          in a pending state

        :type polling_interval: float
        :param polling_interval: polling interval in seconds

        :type break_on_error: bool
        :param break_on_error: whether to break as soon as at least one
          of the returned datasets is in the 'error' state

        :rtype: tuple
        :return: list of output datasets, output history

        The ``params`` dict should be specified as follows::

          {STEP_ID: PARAM_DICT, ...}

        where PARAM_DICT is::

          {PARAM_NAME: VALUE, ...}

        For backwards compatibility, the following (deprecated) format is
        also supported for ``params``::

          {TOOL_ID: PARAM_DICT, ...}

        in which case PARAM_DICT affects all steps with the given tool id.
        If both by-tool-id and by-step-id specifications are used, the
        latter takes precedence.

        Finally (again, for backwards compatibility), PARAM_DICT can also
        be specified as::

          {'param': PARAM_NAME, 'value': VALUE}

        Note that this format allows only one parameter to be set per step.

        Example: set 'a' to 1 for the third workflow step::

          params = {workflow.steps[2].id: {'a': 1}}

        .. warning::

          This is a blocking operation that can take a very long time. If
          ``wait`` is set to ``False``, the method will return as soon as the
          workflow has been *scheduled*, otherwise it will wait until the
          workflow has been *run*. With a large number of steps, however, the
          delay may not be negligible even in the former case (e.g. minutes for
          100 steps).
        """
        if not self.is_mapped:
            raise RuntimeError('workflow is not mapped to a Galaxy object')
        if not self.is_runnable:
            missing_tools_str = ', '.join(f"{self.steps[step_id].tool_id}[{step_id}]" for step_id in self.missing_ids)
            raise RuntimeError(f"workflow has missing tools: {missing_tools_str}")
        kwargs = {
            'dataset_map': self.convert_input_map(input_map or {}),
            'params': params,
            'import_inputs_to_history': import_inputs,
            'replacement_params': replacement_params,
        }
        if isinstance(history, History):
            try:
                kwargs['history_id'] = history.id
            except AttributeError:
                raise RuntimeError('history does not have an id')
        elif isinstance(history, str):
            kwargs['history_name'] = history
        else:
            raise TypeError(
                'history must be either a history wrapper or a string')
        res = self.gi.gi.workflows.run_workflow(self.id, **kwargs)
        # res structure: {'history': HIST_ID, 'outputs': [CI_ID, CI_ID, ...]}
        out_hist = self.gi.histories.get(res['history'])
        content_infos_dict = {ci.id: ci for ci in out_hist.content_infos}
        outputs = []
        for output_id in res['outputs']:
            if content_infos_dict[output_id].type == 'file':
                outputs.append(out_hist.get_dataset(output_id))
            elif content_infos_dict[output_id].type == 'collection':
                outputs.append(out_hist.get_dataset_collection(output_id))

        if wait:
            self.gi._wait_datasets(outputs, polling_interval=polling_interval,
                                   break_on_error=break_on_error)
        return outputs, out_hist

    def export(self):
        """
        Export a re-importable representation of the workflow.

        :rtype: dict
        :return: a JSON-serializable dump of the workflow
        """
        return self.gi.gi.workflows.export_workflow_dict(self.id)

    def delete(self):
        """
        Delete this workflow.

        .. warning::
          Deleting a workflow is irreversible - all of the data from
          the workflow will be permanently deleted.
        """
        self.gi.workflows.delete(id_=self.id)
        self.unmap()

    def invoke(self, inputs=None, params=None, history=None,
               import_inputs_to_history=None, replacement_params=None,
               allow_tool_state_corrections=True, inputs_by=None,
               parameters_normalized=False):
        """
        Invoke the workflow. This will cause a workflow to be scheduled
        and return an object describing the workflow invocation.

        :type inputs: dict
        :param inputs: A mapping of workflow inputs to datasets and dataset collections.
                       The datasets source can be a LibraryDatasetDatasetAssociation (``ldda``),
                       LibraryDataset (``ld``), HistoryDatasetAssociation (``hda``), or
                       HistoryDatasetCollectionAssociation (``hdca``).

                       The map must be in the following format:
                       ``{'<input_index>': {'id': <encoded dataset ID>, 'src': '[ldda, ld, hda, hdca]'}}``
                       (e.g. ``{'2': {'id': '29beef4fadeed09f', 'src': 'hda'}}``)

                       This map may also be indexed by the UUIDs of the workflow steps,
                       as indicated by the ``uuid`` property of steps returned from the
                       Galaxy API. Alternatively workflow steps may be addressed by
                       the label that can be set in the workflow editor. If using
                       uuid or label you need to also set the ``inputs_by`` parameter
                       to ``step_uuid`` or ``name``.

        :type params: dict
        :param params: A mapping of non-datasets tool parameters (see below)

        :type history: str
        :param history: The history in which to store the workflow
          output.

        :type import_inputs_to_history: bool
        :param import_inputs_to_history: If ``True``, used workflow inputs will
          be imported into the history. If ``False``, only workflow outputs will
          be visible in the given history.

        :type allow_tool_state_corrections: bool
        :param allow_tool_state_corrections: If True, allow Galaxy to fill in
          missing tool state when running workflows. This may be useful for
          workflows using tools that have changed over time or for workflows
          built outside of Galaxy with only a subset of inputs defined.

        :type replacement_params: dict
        :param replacement_params: pattern-based replacements for post-job
          actions (see below)

        :type inputs_by: str
        :param inputs_by: Determines how inputs are referenced. Can be
          "step_index|step_uuid" (default), "step_index", "step_id", "step_uuid", or "name".

        :type parameters_normalized: bool
        :param parameters_normalized: Whether Galaxy should normalize ``params``
          to ensure everything is referenced by a numeric step ID. Default is
          ``False``, but when setting ``params`` for a subworkflow, ``True`` is
          required.

        :rtype: Invocation
        :return: the workflow invocation

        The ``params`` dict should be specified as follows::

          {STEP_ID: PARAM_DICT, ...}

        where PARAM_DICT is::

          {PARAM_NAME: VALUE, ...}

        For backwards compatibility, the following (deprecated) format is
        also supported for ``params``::

          {TOOL_ID: PARAM_DICT, ...}

        in which case PARAM_DICT affects all steps with the given tool id.
        If both by-tool-id and by-step-id specifications are used, the
        latter takes precedence.

        Finally (again, for backwards compatibility), PARAM_DICT can also
        be specified as::

          {'param': PARAM_NAME, 'value': VALUE}

        Note that this format allows only one parameter to be set per step.

        For a ``repeat`` parameter, the names of the contained parameters needs
        to be specified as ``<repeat name>_<repeat index>|<param name>``, with
        the repeat index starting at 0. For example, if the tool XML contains::

          <repeat name="cutoff" title="Parameters used to filter cells" min="1">
              <param name="name" type="text" value="n_genes" label="Name of param...">
                  <option value="n_genes">n_genes</option>
                  <option value="n_counts">n_counts</option>
              </param>
              <param name="min" type="float" min="0" value="0" label="Min value"/>
          </repeat>

        then the PARAM_DICT should be something like::

          {...
           "cutoff_0|name": "n_genes",
           "cutoff_0|min": "2",
           "cutoff_1|name": "n_counts",
           "cutoff_1|min": "4",
           ...}

        At the time of this writing, it is not possible to change the number of
        times the contained parameters are repeated. Therefore, the parameter
        indexes can go from 0 to n-1, where n is the number of times the
        repeated element was added when the workflow was saved in the Galaxy UI.

        The ``replacement_params`` dict should map parameter names in
        post-job actions (PJAs) to their runtime values. For
        instance, if the final step has a PJA like the following::

          {'RenameDatasetActionout_file1': {'action_arguments': {'newname': '${output}'},
                                            'action_type': 'RenameDatasetAction',
                                            'output_name': 'out_file1'}}

        then the following renames the output dataset to 'foo'::

          replacement_params = {'output': 'foo'}

        see also `this email thread
        <http://lists.bx.psu.edu/pipermail/galaxy-dev/2011-September/006875.html>`_.

        .. warning::
          Historically, the ``run_workflow`` method consumed a ``dataset_map``
          data structure that was indexed by unencoded workflow step IDs. These
          IDs would not be stable across Galaxy instances. The new ``inputs``
          property is instead indexed by either the ``order_index`` property
          (which is stable across workflow imports) or the step UUID which is
          also stable.
        """
        inv_dict = self.gi.gi.workflows.invoke_workflow(
            workflow_id=self.id,
            inputs=inputs,
            params=params,
            history_id=history.id,
            import_inputs_to_history=import_inputs_to_history,
            replacement_params=replacement_params,
            allow_tool_state_corrections=allow_tool_state_corrections,
            inputs_by=inputs_by,
            parameters_normalized=parameters_normalized
        )
        return self.gi.invocations.get(inv_dict['id'])


class Invocation(Wrapper):
    """
    Invocation of a workflow.
    This causes the steps of a workflow to be executed in sequential order.
    """
    BASE_ATTRS = Wrapper.BASE_ATTRS + (
        'history_id',
        'inputs',
        'state',
        'steps',
        'update_time',
        'uuid',
        'workflow_id',
    )

    def __init__(self, inv_dict, gi=None):
        super().__init__(inv_dict, gi=gi)
        self.steps = [InvocationStep(step, self) for step in self.steps]
        self.inputs = [{**v, 'label': k} for k, v in self.inputs.items()]

    def sorted_step_ids(self):
        """
        Get the step IDs sorted based on this order index.

        :rtype: list of str
        :param: sorted step IDs
        """
        return [step.id for step in sorted(self.steps, key=lambda step: step.order_index)]

    def step_states(self):
        """
        Get the set of step states for this invocation.

        :rtype: set
        :param: step states
        """
        return {step.state for step in self.steps}

    def number_of_steps(self):
        """
        Get the number of steps for this invocation.

        :rtype: int
        :param: number of steps
        """
        return len(self.steps)

    def sorted_steps_by(self, indices=None, states=None, step_ids=None):
        """
        Get steps for this invocation, or get a subset by specifying
        optional parameters for filtering.

        :type indices: list of int
        :param indices: return steps that have matching order_index

        :type states: list of str
        :param states: return steps that have matching states

        :type step_ids: list of str
        :param step_ids: return steps that have matching step_ids

        :rtype: list of InvocationStep
        :param: invocation steps
        """
        steps = self.steps
        if indices is not None:
            steps = filter(lambda step: step.order_index in indices, steps)
        if states is not None:
            steps = filter(lambda step: step.state in states, steps)
        if step_ids is not None:
            steps = filter(lambda step: step.id in step_ids, steps)
        return sorted(steps, key=lambda step: step.order_index)

    def cancel(self):
        """
        Cancel this invocation.

        .. note::
          On success, this method updates the Invocation object's internal variables.
        """
        inv_dict = self.gi.gi.invocations.cancel_invocation(self.id)
        self.__init__(inv_dict, gi=self.gi)

    def refresh(self):
        """
        Update this invocation with the latest information from the server.

        .. note::
          On success, this method updates the Invocation object's internal variables.
        """
        inv_dict = self.gi.gi.invocations.show_invocation(self.id)
        self.__init__(inv_dict, gi=self.gi)

    def run_step_actions(self, steps, actions):
        """
        Run actions for active steps of this invocation.

        :type steps: list of InvocationStep
        :param steps: list of steps to run actions on

        :type actions: list of str
        :param actions: list of actions to run

        .. note::
          On success, this method updates the Invocation object's internal step variables.
        """
        if not len(steps) == len(actions):
            raise RuntimeError(f'Different number of ``steps`` ({len(steps)}) and ``actions`` ({len(actions)}) in ``{self}.run_step_actions()``')
        step_dict_list = [self.gi.gi.invocations.run_invocation_step_action(self.id, step.id, action) for step, action in zip(steps, actions)]
        for step, step_dict in zip(steps, step_dict_list):
            step.__init__(step_dict, parent=self)

    def summary(self):
        """
        Get a summary for this invocation.

        :rtype: dict
        :param: invocation summary
        """
        return self.gi.gi.invocations.get_invocation_summary(self.id)

    def step_jobs_summary(self):
        """
        Get a summary for this invocation's step jobs.

        :rtype: list of dicts
        :param: step job summaries
        """
        return self.gi.gi.invocations.get_invocation_step_jobs_summary(self.id)

    def report(self):
        """
        Get a dictionary containing a Markdown report for this invocation.

        :rtype: dict
        :param: invocation report
        """
        return self.gi.gi.invocations.get_invocation_report(self.id)

    def save_report_pdf(self, file_path, chunk_size=bioblend.CHUNK_SIZE):
        """
        Download a PDF report for this invocation.

        :type file_path: str
        :param file_path: path to save the report

        :type chunk_size: int
        :param chunk_size: chunk size in bytes for reading remote data
        """
        self.gi.gi.invocations.get_invocation_report_pdf(self.id, file_path, chunk_size)

    def biocompute_object(self):
        """
        Get a BioCompute object for this invocation.

        :rtype: dict
        :param: BioCompute object
        """
        return self.gi.gi.invocations.get_invocation_biocompute_object(self.id)

    def wait(self, maxwait=12000, interval=3, check=True):
        """
        Wait for this invocation to reach a terminal state.

        :type maxwait: float
        :param maxwait: upper limit on waiting time

        :type interval: float
        :param interval: polling interval in secconds

        :type check: bool
        :param check: if ``true``, raise an error if the terminal state is not 'scheduled'

        .. note::
          On success, this method updates the Invocation object's internal variables.
        """
        inv_dict = self.gi.gi.invocations.wait_for_invocation(self.id, maxwait=maxwait, interval=interval, check=check)
        self.__init__(inv_dict, gi=self.gi)


class Dataset(Wrapper, metaclass=abc.ABCMeta):
    """
    Abstract base class for Galaxy datasets.
    """
    BASE_ATTRS = Wrapper.BASE_ATTRS + (
        'data_type',
        'file_ext',
        'file_name',
        'file_size',
        'genome_build',
        'misc_info',
        'name',
        'state',
    )
    POLLING_INTERVAL = 1  # for state monitoring

    def __init__(self, ds_dict, container, gi=None):
        super().__init__(ds_dict, gi=gi)
        object.__setattr__(self, 'container', container)

    @property
    @abc.abstractmethod
    def _stream_url(self):
        """
        Return the URL to stream this dataset.
        """
        pass

    def get_stream(self, chunk_size=bioblend.CHUNK_SIZE):
        """
        Open dataset for reading and return an iterator over its contents.

        :type chunk_size: int
        :param chunk_size: read this amount of bytes at a time
        """
        kwargs = {'stream': True}
        if isinstance(self, LibraryDataset):
            kwargs['params'] = {'ld_ids%5B%5D': self.id}
        r = self.gi.gi.make_get_request(self._stream_url, **kwargs)
        if isinstance(self, LibraryDataset) and r.status_code == 500:
            # compatibility with older Galaxy releases
            kwargs['params'] = {'ldda_ids%5B%5D': self.id}
            r = self.gi.gi.make_get_request(self._stream_url, **kwargs)
        r.raise_for_status()
        return r.iter_content(chunk_size)  # FIXME: client can't close r

    def peek(self, chunk_size=bioblend.CHUNK_SIZE):
        """
        Open dataset for reading and return the first chunk.

        See :meth:`.get_stream` for param info.
        """
        try:
            return next(self.get_stream(chunk_size=chunk_size))
        except StopIteration:
            return b''

    def download(self, file_object, chunk_size=bioblend.CHUNK_SIZE):
        """
        Open dataset for reading and save its contents to ``file_object``.

        :type file_object: file
        :param file_object: output file object

        See :meth:`.get_stream` for info on other params.
        """
        for chunk in self.get_stream(chunk_size=chunk_size):
            file_object.write(chunk)

    def get_contents(self, chunk_size=bioblend.CHUNK_SIZE):
        """
        Open dataset for reading and return its **full** contents.

        See :meth:`.get_stream` for param info.
        """
        return b''.join(self.get_stream(chunk_size=chunk_size))

    def refresh(self):
        """
        Re-fetch the attributes pertaining to this object.

        Returns: self
        """
        gi_client = getattr(self.gi.gi, self.container.API_MODULE)
        ds_dict = gi_client.show_dataset(self.container.id, self.id)
        self.__init__(ds_dict, self.container, self.gi)
        return self

    def wait(self, polling_interval=POLLING_INTERVAL, break_on_error=True):
        """
        Wait for this dataset to come out of the pending states.

        :type polling_interval: float
        :param polling_interval: polling interval in seconds

        :type break_on_error: bool
        :param break_on_error: if ``True``, raise a RuntimeError exception if
          the dataset ends in the 'error' state.

        .. warning::

          This is a blocking operation that can take a very long time. Also,
          note that this method does not return anything; however, this dataset
          is refreshed (possibly multiple times) during the execution.
        """
        self.gi._wait_datasets([self], polling_interval=polling_interval,
                               break_on_error=break_on_error)


class HistoryDatasetAssociation(Dataset):
    """
    Maps to a Galaxy ``HistoryDatasetAssociation``.
    """
    BASE_ATTRS = Dataset.BASE_ATTRS + ('annotation', 'deleted', 'purged', 'tags', 'visible')
    SRC = 'hda'

    @property
    def _stream_url(self):
        base_url = self.gi.gi.histories._make_url(module_id=self.container.id, contents=True)
        return f"{base_url}/{self.id}/display"

    def update(self, **kwds):
        """
        Update this history dataset metadata. Some of the attributes that can be
        modified are documented below.

        :type name: str
        :param name: Replace history dataset name with the given string

        :type genome_build: str
        :param genome_build: Replace history dataset genome build (dbkey)

        :type annotation: str
        :param annotation: Replace history dataset annotation with given string

        :type deleted: bool
        :param deleted: Mark or unmark history dataset as deleted

        :type visible: bool
        :param visible: Mark or unmark history dataset as visible
        """
        res = self.gi.gi.histories.update_dataset(self.container.id, self.id, **kwds)
        # Refresh also the history because the dataset may have been (un)deleted
        self.container.refresh()
        self.__init__(res, self.container, gi=self.gi)
        return self

    def delete(self, purge=False):
        """
        Delete this history dataset.

        :type purge: bool
        :param purge: if ``True``, also purge (permanently delete) the dataset

        .. note::
            For the purge option to work, the Galaxy instance must have the
            ``allow_user_dataset_purge`` option set to ``true`` in the
            ``config/galaxy.yml`` configuration file.
        """
        self.gi.gi.histories.delete_dataset(self.container.id, self.id, purge=purge)
        self.container.refresh()
        self.refresh()


class DatasetCollection(Wrapper, metaclass=abc.ABCMeta):
    """
    Abstract base class for Galaxy dataset collections.
    """
    BASE_ATTRS = Wrapper.BASE_ATTRS + (
        'collection_type',
        'deleted',
        'name',
        'state',
    )

    def __init__(self, dsc_dict, container, gi=None):
        super().__init__(dsc_dict, gi=gi)
        object.__setattr__(self, 'container', container)

    def refresh(self):
        """
        Re-fetch the attributes pertaining to this object.

        Returns: self
        """
        gi_client = getattr(self.gi.gi, self.container.API_MODULE)
        dsc_dict = gi_client.show_dataset_collection(self.container.id, self.id)
        self.__init__(dsc_dict, self.container, self.gi)
        return self

    @abc.abstractmethod
    def delete(self):
        pass


class HistoryDatasetCollectionAssociation(DatasetCollection):
    """
    Maps to a Galaxy ``HistoryDatasetCollectionAssociation``.
    """
    BASE_ATTRS = DatasetCollection.BASE_ATTRS + ('tags', 'visible', 'elements')
    SRC = 'hdca'

    def delete(self):
        """
        Delete this dataset collection.
        """
        self.gi.gi.histories.delete_dataset_collection(self.container.id, self.id)
        self.container.refresh()
        self.refresh()


@abstractclass
class LibRelatedDataset(Dataset):
    """
    Base class for LibraryDatasetDatasetAssociation and LibraryDataset classes.
    """

    @property
    def _stream_url(self):
        base_url = self.gi.gi.libraries._make_url()
        return f"{base_url}/datasets/download/uncompressed"


class LibraryDatasetDatasetAssociation(LibRelatedDataset):
    """
    Maps to a Galaxy ``LibraryDatasetDatasetAssociation``.
    """
    BASE_ATTRS = LibRelatedDataset.BASE_ATTRS + ('deleted',)
    SRC = 'ldda'


class LibraryDataset(LibRelatedDataset):
    """
    Maps to a Galaxy ``LibraryDataset``.
    """
    SRC = 'ld'

    def delete(self, purged=False):
        """
        Delete this library dataset.

        :type purged: bool
        :param purged: if ``True``, also purge (permanently delete) the dataset
        """
        self.gi.gi.libraries.delete_library_dataset(
            self.container.id, self.id, purged=purged)
        self.container.refresh()
        self.refresh()

    def update(self, **kwds):
        """
        Update this library dataset metadata. Some of the attributes that can be
        modified are documented below.

        :type name: str
        :param name: Replace history dataset name with the given string

        :type genome_build: str
        :param genome_build: Replace history dataset genome build (dbkey)
        """
        res = self.gi.gi.libraries.update_library_dataset(self.id, **kwds)
        self.container.refresh()
        self.__init__(res, self.container, gi=self.gi)
        return self


@abstractclass
class ContentInfo(Wrapper):
    """
    Instances of this class wrap dictionaries obtained by getting
    ``/api/{histories,libraries}/<ID>/contents`` from Galaxy.
    """
    BASE_ATTRS = Wrapper.BASE_ATTRS + (
        'name',
        'type',
    )


class LibraryContentInfo(ContentInfo):
    """
    Instances of this class wrap dictionaries obtained by getting
    ``/api/libraries/<ID>/contents`` from Galaxy.
    """


class HistoryContentInfo(ContentInfo):
    """
    Instances of this class wrap dictionaries obtained by getting
    ``/api/histories/<ID>/contents`` from Galaxy.
    """
    BASE_ATTRS = ContentInfo.BASE_ATTRS + ('deleted', 'state', 'visible')


class DatasetContainer(Wrapper, metaclass=abc.ABCMeta):
    """
    Abstract base class for dataset containers (histories and libraries).
    """
    BASE_ATTRS = Wrapper.BASE_ATTRS + (
        'deleted',
        'name',
    )

    def __init__(self, c_dict, content_infos=None, gi=None):
        """
        :type content_infos: list of :class:`ContentInfo`
        :param content_infos: info objects for the container's contents
        """
        super().__init__(c_dict, gi=gi)
        if content_infos is None:
            content_infos = []
        object.__setattr__(self, 'content_infos', content_infos)
        object.__setattr__(self, 'obj_gi_client', getattr(self.gi, self.API_MODULE))

    @property
    @abc.abstractmethod
    def API_MODULE(self):
        pass

    @property
    def dataset_ids(self):
        """
        Return the ids of the contained datasets.
        """
        return [_.id for _ in self.content_infos if _.type == 'file']

    def preview(self):
        getf = self.obj_gi_client.get_previews
        # self.state could be stale: check both regular and deleted containers
        try:
            p = [_ for _ in getf() if _.id == self.id][0]
        except IndexError:
            try:
                p = [_ for _ in getf(deleted=True) if _.id == self.id][0]
            except IndexError:
                raise ValueError(f"no object for id {self.id}")
        return p

    def refresh(self):
        """
        Re-fetch the attributes pertaining to this object.

        Returns: self
        """
        fresh = self.obj_gi_client.get(self.id)
        self.__init__(
            fresh.wrapped, content_infos=fresh.content_infos, gi=self.gi)
        return self

    def get_dataset(self, ds_id):
        """
        Retrieve the dataset corresponding to the given id.

        :type ds_id: str
        :param ds_id: dataset id

        :rtype: :class:`~.HistoryDatasetAssociation` or
          :class:`~.LibraryDataset`
        :return: the dataset corresponding to ``ds_id``
        """
        gi_client = getattr(self.gi.gi, self.API_MODULE)
        ds_dict = gi_client.show_dataset(self.id, ds_id)
        return self.DS_TYPE(ds_dict, self, gi=self.gi)

    def get_datasets(self, name=None):
        """
        Get all datasets contained inside this dataset container.

        :type name: str
        :param name: return only datasets with this name

        :rtype: list of :class:`~.HistoryDatasetAssociation` or list of
          :class:`~.LibraryDataset`
        :return: datasets with the given name contained inside this
          container

        .. note::

          when filtering library datasets by name, specify their full
          paths starting from the library's root folder, e.g.,
          ``/seqdata/reads.fastq``.  Full paths are available through
          the ``content_infos`` attribute of
          :class:`~.Library` objects.
        """
        if name is None:
            ds_ids = self.dataset_ids
        else:
            ds_ids = [_.id for _ in self.content_infos if _.name == name]
        return [self.get_dataset(_) for _ in ds_ids]


class History(DatasetContainer):
    """
    Maps to a Galaxy history.
    """
    BASE_ATTRS = DatasetContainer.BASE_ATTRS + ('annotation', 'published', 'state', 'state_ids', 'state_details', 'tags')
    DS_TYPE = HistoryDatasetAssociation
    DSC_TYPE = HistoryDatasetCollectionAssociation
    CONTENT_INFO_TYPE = HistoryContentInfo
    API_MODULE = 'histories'

    def update(self, **kwds):
        """
        Update history metadata information. Some of the attributes that can be
        modified are documented below.

        :type name: str
        :param name: Replace history name with the given string

        :type annotation: str
        :param annotation: Replace history annotation with the given string

        :type deleted: bool
        :param deleted: Mark or unmark history as deleted

        :type purged: bool
        :param purged: If True, mark history as purged (permanently deleted).

        :type published: bool
        :param published: Mark or unmark history as published

        :type importable: bool
        :param importable: Mark or unmark history as importable

        :type tags: list
        :param tags: Replace history tags with the given list
        """
        # TODO: wouldn't it be better if name and annotation were attributes?
        self.gi.gi.histories.update_history(self.id, **kwds)
        self.refresh()
        return self

    def delete(self, purge=False):
        """
        Delete this history.

        :type purge: bool
        :param purge: if ``True``, also purge (permanently delete) the history

        .. note::
          For the purge option to work, the Galaxy instance must have the
          ``allow_user_dataset_purge`` option set to ``true`` in the
          ``config/galaxy.yml`` configuration file.
        """
        self.gi.histories.delete(id_=self.id, purge=purge)
        self.refresh()
        self.unmap()

    def import_dataset(self, lds):
        """
        Import a dataset into the history from a library.

        :type lds: :class:`~.LibraryDataset`
        :param lds: the library dataset to import

        :rtype: :class:`~.HistoryDatasetAssociation`
        :return: the imported history dataset
        """
        if not self.is_mapped:
            raise RuntimeError('history is not mapped to a Galaxy object')
        if not isinstance(lds, LibraryDataset):
            raise TypeError('lds is not a LibraryDataset')
        res = self.gi.gi.histories.upload_dataset_from_library(self.id, lds.id)
        if not isinstance(res, Mapping):
            raise RuntimeError(
                f"upload_dataset_from_library: unexpected reply: {res!r}"
            )
        self.refresh()
        return self.get_dataset(res['id'])

    def upload_file(self, path, **kwargs):
        """
        Upload the file specified by ``path`` to this history.

        :type path: str
        :param path: path of the file to upload

        See :meth:`~bioblend.galaxy.tools.ToolClient.upload_file` for
        the optional parameters.

        :rtype: :class:`~.HistoryDatasetAssociation`
        :return: the uploaded dataset
        """
        out_dict = self.gi.gi.tools.upload_file(path, self.id, **kwargs)
        self.refresh()
        return self.get_dataset(out_dict['outputs'][0]['id'])

    upload_dataset = upload_file

    def upload_from_ftp(self, path, **kwargs):
        """
        Upload the file specified by ``path`` from the user's FTP directory to
        this history.

        :type path: str
        :param path: path of the file in the user's FTP directory

        See :meth:`~bioblend.galaxy.tools.ToolClient.upload_file` for
        the optional parameters.

        :rtype: :class:`~.HistoryDatasetAssociation`
        :return: the uploaded dataset
        """
        out_dict = self.gi.gi.tools.upload_from_ftp(path, self.id, **kwargs)
        self.refresh()
        return self.get_dataset(out_dict['outputs'][0]['id'])

    def paste_content(self, content, **kwargs):
        """
        Upload a string to a new dataset in this history.

        :type content: str
        :param content: content of the new dataset to upload

        See :meth:`~bioblend.galaxy.tools.ToolClient.upload_file` for
        the optional parameters (except file_name).

        :rtype: :class:`~.HistoryDatasetAssociation`
        :return: the uploaded dataset
        """
        out_dict = self.gi.gi.tools.paste_content(content, self.id, **kwargs)
        self.refresh()
        return self.get_dataset(out_dict['outputs'][0]['id'])

    def export(self, gzip=True, include_hidden=False, include_deleted=False,
               wait=False, maxwait=None):
        """
        Start a job to create an export archive for this history.  See
        :meth:`~bioblend.galaxy.histories.HistoryClient.export_history`
        for parameter and return value info.
        """
        return self.gi.gi.histories.export_history(
            self.id, gzip=gzip, include_hidden=include_hidden,
            include_deleted=include_deleted, wait=wait, maxwait=maxwait)

    def download(self, jeha_id, outf, chunk_size=bioblend.CHUNK_SIZE):
        """
        Download an export archive for this history.  Use :meth:`export`
        to create an export and get the required ``jeha_id``.  See
        :meth:`~bioblend.galaxy.histories.HistoryClient.download_history`
        for parameter and return value info.
        """
        return self.gi.gi.histories.download_history(
            self.id, jeha_id, outf, chunk_size=chunk_size)

    def create_dataset_collection(self, collection_description):
        """
        Create a new dataset collection in the history by providing a collection description.

        :type collection_description: bioblend.galaxy.dataset_collections.CollectionDescription
        :param collection_description: a description of the dataset collection

        :rtype: :class:`~.HistoryDatasetCollectionAssociation`
        :return: the new dataset collection
        """
        dataset_collection = self.gi.gi.histories.create_dataset_collection(self.id, collection_description)
        self.refresh()
        return self.get_dataset_collection(dataset_collection['id'])

    def get_dataset_collection(self, dsc_id):
        """
        Retrieve the dataset collection corresponding to the given id.

        :type dsc_id: str
        :param dsc_id: dataset collection id

        :rtype: :class:`~.HistoryDatasetCollectionAssociation`
        :return: the dataset collection corresponding to ``dsc_id``
        """
        dsc_dict = self.gi.gi.histories.show_dataset_collection(self.id, dsc_id)
        return self.DSC_TYPE(dsc_dict, self, gi=self.gi)


class Library(DatasetContainer):
    """
    Maps to a Galaxy library.
    """
    BASE_ATTRS = DatasetContainer.BASE_ATTRS + ('description', 'synopsis')
    DS_TYPE = LibraryDataset
    CONTENT_INFO_TYPE = LibraryContentInfo
    API_MODULE = 'libraries'

    @property
    def folder_ids(self):
        """
        Return the ids of the contained folders.
        """
        return [_.id for _ in self.content_infos if _.type == 'folder']

    def delete(self):
        """
        Delete this library.
        """
        self.gi.libraries.delete(id_=self.id)
        self.refresh()
        self.unmap()

    def _pre_upload(self, folder):
        """
        Return the id of the given folder, after sanity checking.
        """
        if not self.is_mapped:
            raise RuntimeError('library is not mapped to a Galaxy object')
        return None if folder is None else folder.id

    def upload_data(self, data, folder=None, **kwargs):
        """
        Upload data to this library.

        :type data: str
        :param data: dataset contents

        :type folder: :class:`~.Folder`
        :param folder: a folder object, or ``None`` to upload to the root folder

        :rtype: :class:`~.LibraryDataset`
        :return: the dataset object that represents the uploaded content

        Optional keyword arguments: ``file_type``, ``dbkey``.
        """
        fid = self._pre_upload(folder)
        res = self.gi.gi.libraries.upload_file_contents(
            self.id, data, folder_id=fid, **kwargs)
        self.refresh()
        return self.get_dataset(res[0]['id'])

    def upload_from_url(self, url, folder=None, **kwargs):
        """
        Upload data to this library from the given URL.

        :type url: str
        :param url: URL from which data should be read

        See :meth:`.upload_data` for info on other params.
        """
        fid = self._pre_upload(folder)
        res = self.gi.gi.libraries.upload_file_from_url(
            self.id, url, folder_id=fid, **kwargs)
        self.refresh()
        return self.get_dataset(res[0]['id'])

    def upload_from_local(self, path, folder=None, **kwargs):
        """
        Upload data to this library from a local file.

        :type path: str
        :param path: local file path from which data should be read

        See :meth:`.upload_data` for info on other params.
        """
        fid = self._pre_upload(folder)
        res = self.gi.gi.libraries.upload_file_from_local_path(
            self.id, path, folder_id=fid, **kwargs)
        self.refresh()
        return self.get_dataset(res[0]['id'])

    def upload_from_galaxy_fs(self, paths, folder=None, link_data_only=None, **kwargs):
        """
        Upload data to this library from filesystem paths on the server.

        .. note::
          For this method to work, the Galaxy instance must have the
          ``allow_path_paste`` option set to ``true`` in the
          ``config/galaxy.yml`` configuration file.

        :type paths: str or :class:`~collections.abc.Iterable` of str
        :param paths: server-side file paths from which data should be read

        :type link_data_only: str
        :param link_data_only: either 'copy_files' (default) or
          'link_to_files'. Setting to 'link_to_files' symlinks instead of
          copying the files

        :rtype: list of :class:`~.LibraryDataset`
        :return: the dataset objects that represent the uploaded content

        See :meth:`.upload_data` for info on other params.
        """
        fid = self._pre_upload(folder)
        if isinstance(paths, str):
            paths = (paths,)
        paths = '\n'.join(paths)
        res = self.gi.gi.libraries.upload_from_galaxy_filesystem(
            self.id, paths, folder_id=fid, link_data_only=link_data_only,
            **kwargs)
        if res is None:
            raise RuntimeError('upload_from_galaxy_filesystem: no reply')
        if not isinstance(res, Sequence):
            raise RuntimeError(
                f"upload_from_galaxy_filesystem: unexpected reply: {res!r}"
            )
        new_datasets = [
            self.get_dataset(ds_info['id']) for ds_info in res
        ]
        self.refresh()
        return new_datasets

    def copy_from_dataset(self, hda, folder=None, message=''):
        """
        Copy a history dataset into this library.

        :type hda: :class:`~.HistoryDatasetAssociation`
        :param hda: history dataset to copy into the library

        See :meth:`.upload_data` for info on other params.
        """
        fid = self._pre_upload(folder)
        res = self.gi.gi.libraries.copy_from_dataset(
            self.id, hda.id, folder_id=fid, message=message)
        self.refresh()
        return self.get_dataset(res['library_dataset_id'])

    def create_folder(self, name, description=None, base_folder=None):
        """
        Create a folder in this library.

        :type name: str
        :param name: folder name

        :type description: str
        :param description: optional folder description

        :type base_folder: :class:`~.Folder`
        :param base_folder: parent folder, or ``None`` to create in the root
          folder

        :rtype: :class:`~.Folder`
        :return: the folder just created
        """
        bfid = None if base_folder is None else base_folder.id
        res = self.gi.gi.libraries.create_folder(
            self.id, name, description=description, base_folder_id=bfid)
        self.refresh()
        return self.get_folder(res[0]['id'])

    def get_folder(self, f_id):
        """
        Retrieve the folder corresponding to the given id.

        :rtype: :class:`~.Folder`
        :return: the folder corresponding to ``f_id``
        """
        f_dict = self.gi.gi.libraries.show_folder(self.id, f_id)
        return Folder(f_dict, self, gi=self.gi)

    @property
    def root_folder(self):
        """
        The root folder of this library.

        :rtype: :class:`~.Folder`
        :return: the root folder of this library
        """
        return self.get_folder(self.gi.gi.libraries._get_root_folder_id(self.id))


class Folder(Wrapper):
    """
    Maps to a folder in a Galaxy library.
    """
    BASE_ATTRS = Wrapper.BASE_ATTRS + (
        'deleted',
        'description',
        'item_count',
        'name',
    )

    def __init__(self, f_dict, container, gi=None):
        super().__init__(f_dict, gi=gi)
        object.__setattr__(self, 'container', container)

    @property
    def parent(self):
        """
        The parent folder of this folder. The parent of the root folder is
        ``None``.

        :rtype: :class:`~.Folder`
        :return: the parent of this folder
        """
        if self._cached_parent is None:
            object.__setattr__(self,
                               '_cached_parent',
                               self._get_parent())
        return self._cached_parent

    def _get_parent(self):
        """
        Return the parent folder of this folder.
        """
        parent_id = self.wrapped['parent_id']
        if parent_id is None:
            return None
        return self.container.get_folder(parent_id)

    def refresh(self):
        """
        Re-fetch the attributes pertaining to this object.

        Returns: self
        """
        f_dict = self.gi.gi.libraries.show_folder(self.container.id, self.id)
        self.__init__(f_dict, self.container, gi=self.gi)
        return self


class Tool(Wrapper):
    """
    Maps to a Galaxy tool.
    """
    BASE_ATTRS = Wrapper.BASE_ATTRS + (
        'name',
        'version',
    )
    POLLING_INTERVAL = 10  # for output state monitoring

    def run(self, inputs, history, wait=False,
            polling_interval=POLLING_INTERVAL):
        """
        Execute this tool in the given history with inputs from dict
        ``inputs``.

        :type inputs: dict
        :param inputs: dictionary of input datasets and parameters for
          the tool (see below)

        :type history: :class:`History`
        :param history: the history where to execute the tool

        :type wait: bool
        :param wait: whether to wait while the returned datasets are
          in a pending state

        :type polling_interval: float
        :param polling_interval: polling interval in seconds

        :rtype: list of :class:`HistoryDatasetAssociation`
        :return: list of output datasets

        The ``inputs`` dict should contain input datasets and parameters
        in the (largely undocumented) format used by the Galaxy API.
        Some examples can be found in `Galaxy's API test suite
        <https://github.com/galaxyproject/galaxy/blob/dev/lib/galaxy_test/api/test_tools.py>`_.
        The value of an input dataset can also be a :class:`Dataset`
        object, which will be automatically converted to the needed
        format.
        """
        for k, v in inputs.items():
            if isinstance(v, Dataset):
                inputs[k] = {'src': v.SRC, 'id': v.id}
        out_dict = self.gi.gi.tools.run_tool(history.id, self.id, inputs)
        outputs = [history.get_dataset(_['id']) for _ in out_dict['outputs']]
        if wait:
            self.gi._wait_datasets(outputs, polling_interval=polling_interval)
        return outputs


class Job(Wrapper):
    """
    Maps to a Galaxy job.
    """
    BASE_ATTRS = Wrapper.BASE_ATTRS + ('state',)


@abstractclass
class DatasetContainerPreview(Wrapper):
    """
    Abstract base class for dataset container (history and library) 'previews'.
    """
    BASE_ATTRS = Wrapper.BASE_ATTRS + (
        'deleted',
        'name',
    )


class LibraryPreview(DatasetContainerPreview):
    """
    Models Galaxy library 'previews'.

    Instances of this class wrap dictionaries obtained by getting
    ``/api/libraries`` from Galaxy.
    """


class HistoryPreview(DatasetContainerPreview):
    """
    Models Galaxy history 'previews'.

    Instances of this class wrap dictionaries obtained by getting
    ``/api/histories`` from Galaxy.
    """
    BASE_ATTRS = DatasetContainerPreview.BASE_ATTRS + (
        'annotation',
        'published',
        'purged',
        'tags',
    )


class WorkflowPreview(Wrapper):
    """
    Models Galaxy workflow 'previews'.

    Instances of this class wrap dictionaries obtained by getting
    ``/api/workflows`` from Galaxy.
    """
    BASE_ATTRS = Wrapper.BASE_ATTRS + (
        'deleted',
        'latest_workflow_uuid',
        'name',
        'number_of_steps',
        'owner',
        'published',
        'show_in_tool_panel',
        'tags',
    )


class InvocationPreview(Wrapper):
    """
    Models Galaxy invocation 'previews'.

    Instances of this class wrap dictionaries obtained by getting
    ``/api/invocations`` from Galaxy.
    """
    BASE_ATTRS = Wrapper.BASE_ATTRS + (
        'history_id',
        'id',
        'state',
        'update_time',
        'uuid',
        'workflow_id',
    )


class JobPreview(Wrapper):
    """
    Models Galaxy job 'previews'.

    Instances of this class wrap dictionaries obtained by getting
    ``/api/jobs`` from Galaxy.
    """
    BASE_ATTRS = Wrapper.BASE_ATTRS + ('state',)
