# pylint: disable=W0622,E1101

"""
A basic object-oriented interface for Galaxy entities.
"""

import abc
import collections
import json

from six.moves import http_client
import six

import bioblend

__all__ = [
    'Wrapper',
    'Step',
    'Workflow',
    'ContentInfo',
    'LibraryContentInfo',
    'HistoryContentInfo',
    'DatasetContainer',
    'History',
    'Library',
    'Folder',
    'Dataset',
    'HistoryDatasetAssociation',
    'LibraryDatasetDatasetAssociation',
    'LibraryDataset',
    'Tool',
    'Preview',
    'LibraryPreview',
    'HistoryPreview',
    'WorkflowPreview',
]


@six.add_metaclass(abc.ABCMeta)
class Wrapper(object):
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
    BASE_ATTRS = ('id', 'name')

    @abc.abstractmethod
    def __init__(self, wrapped, parent=None, gi=None):
        """
        :type wrapped: dict
        :param wrapped: JSON-serializable dictionary

        :type parent: :class:`Wrapper`
        :param parent: the parent of this wrapper

        :type gi: :class:`GalaxyInstance`
        :param gi: the GalaxyInstance through which we can access this wrapper
        """
        if not isinstance(wrapped, collections.Mapping):
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

    @abc.abstractproperty
    def gi_module(self):
        """
        The GalaxyInstance module that deals with objects of this type.
        """
        pass

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
        return "%s(%r)" % (self.__class__.__name__, self.wrapped)


class Step(Wrapper):
    """
    Abstract base class for workflow steps.

    Steps are the main building blocks of a Galaxy workflow.  A step
    can refer to either an input dataset (type 'data_input`) or a
    computational tool (type 'tool`).
    """
    BASE_ATTRS = Wrapper.BASE_ATTRS + (
        'input_steps', 'tool_id', 'tool_inputs', 'tool_version', 'type'
    )

    def __init__(self, step_dict, parent):
        super(Step, self).__init__(step_dict, parent=parent, gi=parent.gi)
        if self.type == 'tool' and self.tool_inputs:
            for k, v in six.iteritems(self.tool_inputs):
                self.tool_inputs[k] = json.loads(v)

    @property
    def gi_module(self):
        return self.gi.workflows


class Workflow(Wrapper):
    """
    Workflows represent ordered sequences of computations on Galaxy.

    A workflow defines a sequence of steps that produce one or more
    results from an input dataset.
    """
    BASE_ATTRS = Wrapper.BASE_ATTRS + (
        'deleted', 'inputs', 'published', 'steps', 'tags'
    )
    POLLING_INTERVAL = 10  # for output state monitoring

    def __init__(self, wf_dict, gi=None):
        super(Workflow, self).__init__(wf_dict, gi=gi)
        missing_ids = []
        for k, v in six.iteritems(self.steps):
            # convert step ids to str for consistency with outer keys
            v['id'] = str(v['id'])
            for i in six.itervalues(v['input_steps']):
                i['source_step'] = str(i['source_step'])
            step = self._build_step(v, self)
            self.steps[k] = step
            if step.type == 'tool' and not step.tool_inputs:
                missing_ids.append(k)
        input_labels_to_ids = {}
        for id_, d in six.iteritems(self.inputs):
            input_labels_to_ids.setdefault(d['label'], set()).add(id_)
        tool_labels_to_ids = {}
        for s in six.itervalues(self.steps):
            if s.type == 'tool':
                tool_labels_to_ids.setdefault(s.tool_id, set()).add(s.id)
        object.__setattr__(self, 'input_labels_to_ids', input_labels_to_ids)
        object.__setattr__(self, 'tool_labels_to_ids', tool_labels_to_ids)
        dag, inv_dag = self._get_dag()
        heads, tails = set(dag), set(inv_dag)
        object.__setattr__(self, 'dag', dag)
        object.__setattr__(self, 'inv_dag', inv_dag)
        object.__setattr__(self, 'source_ids', heads - tails)
        assert self.data_input_ids == set(self.inputs)
        object.__setattr__(self, 'sink_ids', tails - heads)
        object.__setattr__(self, 'missing_ids', missing_ids)

    @property
    def gi_module(self):
        return self.gi.workflows

    def _get_dag(self):
        """
        Return the workflow's DAG.

        For convenience, this method computes a 'direct' (step =>
        successors) and an 'inverse' (step => predecessors)
        representation of the same DAG.

        For instance, a workflow with a single tool *c*, two inputs
        *a, b* and three outputs *d, e, f* is represented by (direct)::

          {'a': {'c'}, 'b': {'c'}, 'c': set(['d', 'e', 'f'])}

        and by (inverse)::

          {'c': set(['a', 'b']), 'd': {'c'}, 'e': {'c'}, 'f': {'c'}}
        """
        dag, inv_dag = {}, {}
        for s in six.itervalues(self.steps):
            for i in six.itervalues(s.input_steps):
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
        inv_dag = dict((k, v.copy()) for k, v in six.iteritems(self.inv_dag))
        while source_ids:
            head = source_ids.pop()
            ids.append(head)
            for tail in self.dag.get(head, []):
                incoming = inv_dag[tail]
                incoming.remove(head)
                if not incoming:
                    source_ids.add(tail)
        return ids

    @staticmethod
    def _build_step(step_dict, parent):
        """
        Return a Step object for the given parameters.
        """
        try:
            stype = step_dict['type']
        except KeyError:
            raise ValueError('not a step dict')
        if stype not in set(['data_input', 'tool']):
            raise ValueError('unknown step type: %r' % (stype,))
        return Step(step_dict, parent)

    @property
    def data_input_ids(self):
        """
        Return the list of data input steps for this workflow.
        """
        return set(id_ for id_, s in six.iteritems(self.steps)
                   if s.type == 'data_input')

    @property
    def tool_ids(self):
        """
        Return the list of tool steps for this workflow.
        """
        return set(id_ for id_, s in six.iteritems(self.steps)
                   if s.type == 'tool')

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
        for label, slot_ids in six.iteritems(self.input_labels_to_ids):
            datasets = input_map.get(label, [])
            if not isinstance(datasets, collections.Iterable):
                datasets = [datasets]
            if len(datasets) < len(slot_ids):
                raise RuntimeError('not enough datasets for "%s"' % label)
            for id_, ds in zip(slot_ids, datasets):
                m[id_] = {'id': ds.id, 'src': ds.SRC}
        return m

    def preview(self):
        getf = self.gi.workflows.get_previews
        try:
            p = [_ for _ in getf(published=True) if _.id == self.id][0]
        except IndexError:
            raise ValueError('no object for id %s' % self.id)
        return p

    def run(self, input_map=None, history='', params=None, import_inputs=False,
            replacement_params=None, wait=False,
            polling_interval=POLLING_INTERVAL, break_on_error=True):
        """
        Run the workflow in the current Galaxy instance.

        :type input_map: dict
        :param input_map: a mapping from workflow input labels to
          datasets, e.g.: ``dict(zip(workflow.input_labels,
          library.get_datasets()))``

        :type history: :class:`History` or str
        :param history: either a valid history object (results will be
          stored there) or a string (a new history will be created with
          the given name).

        :type params: :class:`~collections.Mapping`
        :param params: parameter settings for workflow steps (see below)

        :type import_inputs: bool
        :param import_inputs: If ``True``, workflow inputs will be imported into
          the history; if ``False``, only workflow outputs will be visible in
          the history.

        :type replacement_params: :class:`~collections.Mapping`
        :param replacement_params: pattern-based replacements for
          post-job actions (see the docs for
          :meth:`~bioblend.galaxy.workflows.WorkflowClient.run_workflow`)

        :type wait: boolean
        :param wait: whether to wait while the returned datasets are
          in a pending state

        :type polling_interval: float
        :param polling_interval: polling interval in seconds

        :type break_on_error: boolean
        :param break_on_error: whether to break as soon as at least one
          of the returned datasets is in the 'error' state

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
            raise RuntimeError('workflow has missing tools: %s' % ', '.join(
                '%s[%s]' % (self.steps[_].tool_id, _)
                for _ in self.missing_ids))
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
        elif isinstance(history, six.string_types):
            kwargs['history_name'] = history
        else:
            raise TypeError(
                'history must be either a history wrapper or a string')
        res = self.gi.gi.workflows.run_workflow(self.id, **kwargs)
        # res structure: {'history': HIST_ID, 'outputs': [DS_ID, DS_ID, ...]}
        out_hist = self.gi.histories.get(res['history'])
        assert set(res['outputs']).issubset(out_hist.dataset_ids)
        outputs = [out_hist.get_dataset(_) for _ in res['outputs']]

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
        return self.gi.gi.workflows.export_workflow_json(self.id)

    def delete(self):
        """
        Delete this workflow.

        .. warning::
          Deleting a workflow is irreversible - all of the data from
          the workflow will be permanently deleted.
        """
        self.gi.workflows.delete(id_=self.id)
        self.unmap()


@six.add_metaclass(abc.ABCMeta)
class Dataset(Wrapper):
    """
    Abstract base class for Galaxy datasets.
    """
    BASE_ATTRS = Wrapper.BASE_ATTRS + (
        'data_type', 'file_name', 'file_size', 'state', 'deleted', 'file_ext'
    )
    POLLING_INTERVAL = 1  # for state monitoring

    @abc.abstractmethod
    def __init__(self, ds_dict, container, gi=None):
        super(Dataset, self).__init__(ds_dict, gi=gi)
        object.__setattr__(self, 'container', container)

    @property
    def container_id(self):
        """
        Deprecated property.

        Id of the dataset container. Use :attr:`.container.id` instead.
        """
        return self.container.id

    @abc.abstractproperty
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

        .. warning::

          Due to a change in the Galaxy API endpoint, this method does
          not work on :class:`LibraryDataset` instances with Galaxy
          ``release_2014.06.02``. Methods that delegate work to this one
          are also affected: :meth:`peek`, :meth:`download` and
          :meth:`get_contents`.
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
    BASE_ATTRS = Dataset.BASE_ATTRS + ('tags', 'visible')
    SRC = 'hda'

    def __init__(self, ds_dict, container, gi=None):
        super(HistoryDatasetAssociation, self).__init__(
            ds_dict, container, gi=gi)

    @property
    def gi_module(self):
        return self.gi.histories

    @property
    def _stream_url(self):
        base_url = self.gi.gi._make_url(
            self.gi.gi.histories, module_id=self.container.id, contents=True)
        return "%s/%s/display" % (base_url, self.id)

    def delete(self):
        """
        Delete this dataset.
        """
        self.gi.gi.histories.delete_dataset(self.container.id, self.id)
        self.container.refresh()
        self.refresh()


class LibRelatedDataset(Dataset):
    """
    Base class for LibraryDatasetDatasetAssociation and LibraryDataset classes.
    """

    def __init__(self, ds_dict, container, gi=None):
        super(LibRelatedDataset, self).__init__(ds_dict, container, gi=gi)

    @property
    def gi_module(self):
        return self.gi.libraries

    @property
    def _stream_url(self):
        base_url = self.gi.gi._make_url(self.gi.gi.libraries)
        return "%s/datasets/download/uncompressed" % base_url


class LibraryDatasetDatasetAssociation(LibRelatedDataset):
    """
    Maps to a Galaxy ``LibraryDatasetDatasetAssociation``.
    """
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


@six.add_metaclass(abc.ABCMeta)
class ContentInfo(Wrapper):
    """
    Instances of this class wrap dictionaries obtained by getting
    ``/api/{histories,libraries}/<ID>/contents`` from Galaxy.
    """
    BASE_ATTRS = Wrapper.BASE_ATTRS + ('type',)

    @abc.abstractmethod
    def __init__(self, info_dict, gi=None):
        super(ContentInfo, self).__init__(info_dict, gi=gi)


class LibraryContentInfo(ContentInfo):
    """
    Instances of this class wrap dictionaries obtained by getting
    ``/api/libraries/<ID>/contents`` from Galaxy.
    """
    def __init__(self, info_dict, gi=None):
        super(LibraryContentInfo, self).__init__(info_dict, gi=gi)

    @property
    def gi_module(self):
        return self.gi.libraries


class HistoryContentInfo(ContentInfo):
    """
    Instances of this class wrap dictionaries obtained by getting
    ``/api/histories/<ID>/contents`` from Galaxy.
    """
    BASE_ATTRS = ContentInfo.BASE_ATTRS + ('deleted', 'state', 'visible')

    def __init__(self, info_dict, gi=None):
        super(HistoryContentInfo, self).__init__(info_dict, gi=gi)

    @property
    def gi_module(self):
        return self.gi.histories


@six.add_metaclass(abc.ABCMeta)
class DatasetContainer(Wrapper):
    """
    Abstract base class for dataset containers (histories and libraries).
    """
    BASE_ATTRS = Wrapper.BASE_ATTRS + ('deleted',)

    @abc.abstractmethod
    def __init__(self, c_dict, content_infos=None, gi=None):
        """
        :type content_infos: list of :class:`ContentInfo`
        :param content_infos: info objects for the container's contents
        """
        super(DatasetContainer, self).__init__(c_dict, gi=gi)
        if content_infos is None:
            content_infos = []
        object.__setattr__(self, 'content_infos', content_infos)

    @property
    def dataset_ids(self):
        """
        Return the ids of the contained datasets.
        """
        return [_.id for _ in self.content_infos if _.type == 'file']

    def preview(self):
        getf = self.gi_module.get_previews
        # self.state could be stale: check both regular and deleted containers
        try:
            p = [_ for _ in getf() if _.id == self.id][0]
        except IndexError:
            try:
                p = [_ for _ in getf(deleted=True) if _.id == self.id][0]
            except IndexError:
                raise ValueError('no object for id %s' % self.id)
        return p

    def refresh(self):
        """
        Re-fetch the attributes pertaining to this object.

        Returns: self
        """
        fresh = self.gi_module.get(self.id)
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
    BASE_ATTRS = DatasetContainer.BASE_ATTRS + ('annotation', 'state', 'state_ids', 'state_details', 'tags')
    DS_TYPE = HistoryDatasetAssociation
    CONTENT_INFO_TYPE = HistoryContentInfo
    API_MODULE = 'histories'

    def __init__(self, hist_dict, content_infos=None, gi=None):
        super(History, self).__init__(
            hist_dict, content_infos=content_infos, gi=gi)

    @property
    def gi_module(self):
        return self.gi.histories

    def update(self, name=None, annotation=None, **kwds):
        """
        Update history metadata information. Some of the attributes that can be
        modified are documented below.

        :type name: string
        :param name: Replace history name with the given string
        :type annotation: string
        :param annotation: Replace history annotation with given string
        :type deleted: boolean
        :param deleted: Mark or unmark history as deleted
        :type published: boolean
        :param published: Mark or unmark history as published
        :type importable: boolean
        :param importable: Mark or unmark history as importable
        :type tags: list
        :param tags: Replace history tags with the given list
        """
        # TODO: wouldn't it be better if name and annotation were attributes?
        # TODO: do we need to ensure the attributes of `self` are the same as
        # the ones returned by the call to `update_history` below?
        res = self.gi.gi.histories.update_history(
            self.id, name=name, annotation=annotation, **kwds)
        if res != http_client.OK:
            raise RuntimeError('failed to update history')
        self.refresh()
        return self

    def delete(self, purge=False):
        """
        Delete this history.

        :type purge: bool
        :param purge: if ``True``, also purge (permanently delete) the history

        .. note::
          For the purge option to work, the Galaxy instance must have the
          ``allow_user_dataset_purge`` option set to ``True`` in the
          ``config/galaxy.ini`` configuration file.
        """
        self.gi.histories.delete(id_=self.id, purge=purge)
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
        if not isinstance(res, collections.Mapping):
            raise RuntimeError(
                'upload_dataset_from_library: unexpected reply: %r' % res)
        self.refresh()
        return self.get_dataset(res['id'])

    def upload_file(self, path, **kwargs):
        """
        Upload the file specified by path to this history.

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
               wait=False):
        """
        Start a job to create an export archive for this history.  See
        :meth:`~bioblend.galaxy.histories.HistoryClient.export_history`
        for parameter and return value info.
        """
        return self.gi.gi.histories.export_history(
            self.id,
            gzip=gzip,
            include_hidden=include_hidden,
            include_deleted=include_deleted,
            wait=wait)

    def download(self, jeha_id, outf, chunk_size=bioblend.CHUNK_SIZE):
        """
        Download an export archive for this history.  Use :meth:`export`
        to create an export and get the required ``jeha_id``.  See
        :meth:`~bioblend.galaxy.histories.HistoryClient.download_history`
        for parameter and return value info.
        """
        return self.gi.gi.histories.download_history(
            self.id, jeha_id, outf, chunk_size=chunk_size)


class Library(DatasetContainer):
    """
    Maps to a Galaxy library.
    """
    BASE_ATTRS = DatasetContainer.BASE_ATTRS + ('description', 'synopsis')
    DS_TYPE = LibraryDataset
    CONTENT_INFO_TYPE = LibraryContentInfo
    API_MODULE = 'libraries'

    def __init__(self, lib_dict, content_infos=None, gi=None):
        super(Library, self).__init__(
            lib_dict, content_infos=content_infos, gi=gi)

    @property
    def gi_module(self):
        return self.gi.libraries

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
        self.unmap()

    def __pre_upload(self, folder):
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
        fid = self.__pre_upload(folder)
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
        fid = self.__pre_upload(folder)
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
        fid = self.__pre_upload(folder)
        res = self.gi.gi.libraries.upload_file_from_local_path(
            self.id, path, folder_id=fid, **kwargs)
        self.refresh()
        return self.get_dataset(res[0]['id'])

    def upload_from_galaxy_fs(self, paths, folder=None, link_data_only=None, **kwargs):
        """
        Upload data to this library from filesystem paths on the server.

        .. note::
          For this method to work, the Galaxy instance must have the
          ``allow_library_path_paste`` option set to ``True`` in the
          ``config/galaxy.ini`` configuration file.

        :type paths: str or :class:`~collections.Iterable` of str
        :param paths: server-side file paths from which data should be read

        :type link_data_only: str
        :param link_data_only: either 'copy_files' (default) or
          'link_to_files'. Setting to 'link_to_files' symlinks instead of
          copying the files

        :rtype: list of :class:`~.LibraryDataset`
        :return: the dataset objects that represent the uploaded content

        See :meth:`.upload_data` for info on other params.
        """
        fid = self.__pre_upload(folder)
        if isinstance(paths, six.string_types):
            paths = (paths,)
        paths = '\n'.join(paths)
        res = self.gi.gi.libraries.upload_from_galaxy_filesystem(
            self.id, paths, folder_id=fid, link_data_only=link_data_only,
            **kwargs)
        if res is None:
            raise RuntimeError('upload_from_galaxy_filesystem: no reply')
        if not isinstance(res, collections.Sequence):
            raise RuntimeError(
                'upload_from_galaxy_filesystem: unexpected reply: %r' % res)
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
        fid = self.__pre_upload(folder)
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
    BASE_ATTRS = Wrapper.BASE_ATTRS + ('description', 'deleted', 'item_count')

    def __init__(self, f_dict, container, gi=None):
        super(Folder, self).__init__(f_dict, gi=gi)
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
        # Galaxy release_13.04 and earlier does not have parent_id in the folder
        # dictionary, may be implemented by searching for the folder with the
        # correct name
        if 'parent_id' not in self.wrapped:
            raise NotImplementedError('This method has not been implemented for Galaxy release_13.04 and earlier')
        parent_id = self.wrapped['parent_id']
        if parent_id is None:
            return None
        # Galaxy from release_14.02 to release_15.01 returns a dummy parent_id
        # for the root folder instead of None, so check if this is the root
        if self.id == self.gi.gi.libraries._get_root_folder_id(self.container.id):
            return None
        # Galaxy release_13.11 and earlier returns a parent_id without the
        # initial 'F'
        if not parent_id.startswith('F'):
            parent_id = 'F' + parent_id
        return self.container.get_folder(parent_id)

    @property
    def gi_module(self):
        return self.gi.libraries

    @property
    def container_id(self):
        """
        Deprecated property.

        Id of the folder container. Use :attr:`.container.id` instead.
        """
        return self.container.id

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
    BASE_ATTRS = Wrapper.BASE_ATTRS + ('version',)
    POLLING_INTERVAL = 10  # for output state monitoring

    def __init__(self, t_dict, gi=None):
        super(Tool, self).__init__(t_dict, gi=gi)

    @property
    def gi_module(self):
        return self.gi.tools

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

        :type wait: boolean
        :param wait: whether to wait while the returned datasets are
          in a pending state

        :type polling_interval: float
        :param polling_interval: polling interval in seconds

        :rtype: list of :class:`HistoryDatasetAssociation`
        :return: list of output datasets

        The ``inputs`` dict should contain input datasets and parameters
        in the (largely undocumented) format used by the Galaxy API.
        Some examples can be found in `Galaxy's API test suite
        <https://bitbucket.org/galaxy/galaxy-central/src/tip/test/api/test_tools.py>`_.
        The value of an input dataset can also be a :class:`Dataset`
        object, which will be automatically converted to the needed
        format.
        """
        for k, v in six.iteritems(inputs):
            if isinstance(v, Dataset):
                inputs[k] = {'src': v.SRC, 'id': v.id}
        out_dict = self.gi.gi.tools.run_tool(history.id, self.id, inputs)
        outputs = [history.get_dataset(_['id']) for _ in out_dict['outputs']]
        if wait:
            self.gi._wait_datasets(outputs, polling_interval=polling_interval)
        return outputs


@six.add_metaclass(abc.ABCMeta)
class Preview(Wrapper):
    """
    Abstract base class for Galaxy entity 'previews'.

    Classes derived from this one model the short summaries returned
    by global getters such as ``/api/libraries``.
    """
    BASE_ATTRS = Wrapper.BASE_ATTRS + ('deleted',)

    @abc.abstractmethod
    def __init__(self, pw_dict, gi=None):
        super(Preview, self).__init__(pw_dict, gi=gi)


class LibraryPreview(Preview):
    """
    Models Galaxy library 'previews'.

    Instances of this class wrap dictionaries obtained by getting
    ``/api/libraries`` from Galaxy.
    """
    def __init__(self, pw_dict, gi=None):
        super(LibraryPreview, self).__init__(pw_dict, gi=gi)

    @property
    def gi_module(self):
        return self.gi.libraries


class HistoryPreview(Preview):
    """
    Models Galaxy history 'previews'.

    Instances of this class wrap dictionaries obtained by getting
    ``/api/histories`` from Galaxy.
    """
    BASE_ATTRS = Preview.BASE_ATTRS + ('tags',)

    def __init__(self, pw_dict, gi=None):
        super(HistoryPreview, self).__init__(pw_dict, gi=gi)

    @property
    def gi_module(self):
        return self.gi.histories


class WorkflowPreview(Preview):
    """
    Models Galaxy workflow 'previews'.

    Instances of this class wrap dictionaries obtained by getting
    ``/api/workflows`` from Galaxy.
    """
    BASE_ATTRS = Preview.BASE_ATTRS + ('published', 'tags')

    def __init__(self, pw_dict, gi=None):
        super(WorkflowPreview, self).__init__(pw_dict, gi=gi)

    @property
    def gi_module(self):
        return self.gi.workflows
