# pylint: disable=W0622,E1101

"""
A basic object-oriented interface for Galaxy entities.
"""

import bioblend
import abc, collections, httplib, json


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


# sometimes the Galaxy API returns JSONs that contain other JSONs
def _recursive_loads(jdef):
    try:
        r = json.loads(jdef)
    except (TypeError, ValueError):
        r = jdef
    if isinstance(r, collections.Sequence) and not isinstance(r, basestring):
        for i, v in enumerate(r):
            r[i] = _recursive_loads(v)
    elif isinstance(r, collections.Mapping):
        for k, v in r.iteritems():
            r[k] = _recursive_loads(v)
    return r


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
    __metaclass__ = abc.ABCMeta

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
        object.__setattr__(self, 'parent', parent)
        object.__setattr__(self, 'is_modified', False)
        object.__setattr__(self, 'gi', gi)

    @abc.abstractproperty
    def gi_module(self):
        """
        The GalaxyInstance module that deals with objects of this type.
        """
        pass

    @property
    def is_mapped(self):
        """
        :obj:`True` if this wrapper is mapped to an actual Galaxy entity.
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
            for k, v in self.tool_inputs.iteritems():
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
        for k, v in self.steps.iteritems():
            # convert step ids to str for consistency with outer keys
            v['id'] = str(v['id'])
            for i in v['input_steps'].itervalues():
                i['source_step'] = str(i['source_step'])
            step = self._build_step(v, self)
            self.steps[k] = step
            if step.type == 'tool' and not step.tool_inputs:
                missing_ids.append(k)
        input_labels_to_ids = {}
        for id_, d in self.inputs.iteritems():
            input_labels_to_ids.setdefault(d['label'], set()).add(id_)
        tool_labels_to_ids = {}
        for s in self.steps.itervalues():
            if s.type == 'tool':
                tool_labels_to_ids.setdefault(s.tool_id, set()).add(s.id)
        object.__setattr__(self, 'input_labels_to_ids', input_labels_to_ids)
        object.__setattr__(self, 'tool_labels_to_ids', tool_labels_to_ids)
        dag, inv_dag = self._get_dag()
        heads, tails = set(dag), set(inv_dag)
        object.__setattr__(self, '_dag', dag)
        object.__setattr__(self, '_inv_dag', inv_dag)
        object.__setattr__(self, 'input_ids', heads - tails)
        assert self.input_ids == set(self.inputs)
        object.__setattr__(self, 'output_ids', tails - heads)
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
        for s in self.steps.itervalues():
            for i in s.input_steps.itervalues():
                head, tail = i['source_step'], s.id
                dag.setdefault(head, set()).add(tail)
                inv_dag.setdefault(tail, set()).add(head)
        return dag, inv_dag

    @property
    def dag(self):
        return self._dag

    @property
    def inv_dag(self):
        return self._inv_dag

    def sorted_step_ids(self):
        """
        Return a topological sort of the workflow's DAG.
        """
        ids = []
        input_ids = self.input_ids.copy()
        inv_dag = dict((k, v.copy()) for k, v in self.inv_dag.iteritems())
        while input_ids:
            head = input_ids.pop()
            ids.append(head)
            for tail in self.dag.get(head, []):
                incoming = inv_dag[tail]
                incoming.remove(head)
                if not incoming:
                    input_ids.add(tail)
        return ids

    @staticmethod
    def _build_step(step_dict, parent):
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
        return set(id_ for id_, s in self.steps.iteritems()
                   if s.type == 'data_input')

    @property
    def tool_ids(self):
        """
        Return the list of tool steps for this workflow.
        """
        return set(id_ for id_, s in self.steps.iteritems()
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
        for label, slot_ids in self.input_labels_to_ids.iteritems():
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
        :param import_inputs: If :obj:`True`, workflow inputs will be
          imported into the history; if :obj:`False`, only workflow
          outputs will be visible in the history.

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
        """
        if not self.is_mapped:
            raise RuntimeError('workflow is not mapped to a Galaxy object')
        if not self.is_runnable:
            raise RuntimeError('workflow has missing tools: %s' % ', '.join(
                '%s[%s]' % (self.steps[_].tool_id, _)
                for _ in self.missing_ids
                ))
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
        elif isinstance(history, basestring):
            kwargs['history_name'] = history
        else:
            raise TypeError(
                'history must be either a history wrapper or a string'
                )
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
        self.gi.workflows.delete(id_=self.id)
        self.unmap()


class Dataset(Wrapper):
    """
    Abstract base class for Galaxy datasets.
    """
    BASE_ATTRS = Wrapper.BASE_ATTRS + (
        'data_type', 'file_name', 'file_size', 'state', 'deleted'
        )
    __metaclass__ = abc.ABCMeta
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
        pass

    def get_stream(self, chunk_size=None):
        """
        Open dataset for reading and return an iterator over its contents.

        :type chunk_size: int
        :param chunk_size: read this amount of bytes at a time
        """
        kwargs = {'stream': True}
        if isinstance(self, LibraryDataset):
            kwargs['params'] = {'ldda_ids%5B%5D': self.id}
        r = self.gi.gi.make_get_request(self._stream_url, **kwargs)
        r.raise_for_status()
        return r.iter_content(chunk_size)  # FIXME: client can't close r

    def peek(self, chunk_size=None):
        """
        Open dataset for reading and return the first chunk.

        See :meth:`.get_stream` for param info.
        """
        try:
            return self.get_stream(chunk_size=chunk_size).next()
        except StopIteration:
            return ''

    def download(self, file_object, chunk_size=None):
        """
        Open dataset for reading and save its contents to ``file_object``.

        :type outf: :obj:`file`
        :param outf: output file object

        See :meth:`.get_stream` for info on other params.
        """
        for chunk in self.get_stream(chunk_size=chunk_size):
            file_object.write(chunk)

    def get_contents(self, chunk_size=None):
        """
        Open dataset for reading and return its **full** contents.

        See :meth:`.get_stream` for param info.
        """
        return ''.join(self.get_stream(chunk_size=chunk_size))

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
        self.gi._wait_datasets([self], polling_interval=polling_interval,
                               break_on_error=break_on_error)


class HistoryDatasetAssociation(Dataset):
    """
    Maps to a Galaxy ``HistoryDatasetAssociation``.
    """
    SRC = 'hda'

    def __init__(self, ds_dict, container, gi=None):
        super(HistoryDatasetAssociation, self).__init__(
            ds_dict, container, gi=gi
            )

    @property
    def gi_module(self):
        return self.gi.histories

    @property
    def _stream_url(self):
        base_url = self.gi.gi._make_url(
            self.gi.gi.histories, module_id=self.container.id, contents=True
            )
        return "%s/%s/display" % (base_url, self.id)


class LibRelatedDataset(Dataset):
    """
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


class ContentInfo(Wrapper):
    """
    Instances of this class wrap dictionaries obtained by getting
    ``/api/{histories,libraries}/<ID>/contents`` from Galaxy.
    """
    BASE_ATTRS = Wrapper.BASE_ATTRS + ('type',)
    __metaclass__ = abc.ABCMeta

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
        if self.id.startswith('F'):
            object.__setattr__(self, 'id', self.id[1:])

    @property
    def gi_module(self):
        return self.gi.libraries


class HistoryContentInfo(ContentInfo):
    """
    Instances of this class wrap dictionaries obtained by getting
    ``/api/histories/<ID>/contents`` from Galaxy.
    """
    def __init__(self, info_dict, gi=None):
        super(HistoryContentInfo, self).__init__(info_dict, gi=gi)

    @property
    def gi_module(self):
        return self.gi.histories


class DatasetContainer(Wrapper):
    """
    Abstract base class for dataset containers (histories and libraries).
    """
    __metaclass__ = abc.ABCMeta

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
            fresh.wrapped, content_infos=fresh.content_infos, gi=self.gi
            )
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
    BASE_ATTRS = DatasetContainer.BASE_ATTRS + ('annotation', 'state_ids')
    DS_TYPE = HistoryDatasetAssociation
    CONTENT_INFO_TYPE = HistoryContentInfo
    API_MODULE = 'histories'

    def __init__(self, hist_dict, content_infos=None, gi=None):
        super(History, self).__init__(
            hist_dict, content_infos=content_infos, gi=gi
            )

    @property
    def gi_module(self):
        return self.gi.histories

    def update(self, name=None, annotation=None):
        """
        Update history metadata with the given name and annotation.
        """
        # TODO: wouldn't it be better if name and annotation were attributes?
        # TODO: do we need to ensure the attributes of `self` are the same as
        # the ones returned by the call to `update_history` below?
        res = self.gi.gi.histories.update_history(
            self.id, name=name, annotation=annotation
            )
        if res != httplib.OK:
            raise RuntimeError('failed to update history')
        self.refresh()
        return self

    def delete(self, purge=False):
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
                'upload_dataset_from_library: unexpected reply: %r' % res
                )
        self.refresh()
        return self.get_dataset(res['id'])

    def upload_dataset(self, path, **kwargs):
        """
        Upload the file specified by path to this history.

        :type path: str
        :param path: path of the file to upload

        :rtype: :class:`~.HistoryDatasetAssociation`
        :return: the uploaded dataset
        """
        out_dict = self.gi.gi.tools.upload_file(path, self.id, **kwargs)
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
            wait=wait
            )

    def download(self, jeha_id, outf, chunk_size=bioblend.CHUNK_SIZE):
        """
        Download an export archive for this history.  Use :meth:`export`
        to create an export and get the required ``jeha_id``.  See
        :meth:`~bioblend.galaxy.histories.HistoryClient.download_history`
        for parameter and return value info.
        """
        return self.gi.gi.histories.download_history(
            self.id, jeha_id, outf, chunk_size=chunk_size
            )


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
            lib_dict, content_infos=content_infos, gi=gi
            )

    @property
    def gi_module(self):
        return self.gi.libraries

    @property
    def folder_ids(self):
        return [_.id for _ in self.content_infos if _.type == 'folder']

    def delete(self):
        self.gi.libraries.delete(id_=self.id)
        self.unmap()

    def upload_data(self, data, folder=None, **kwargs):
        return self.gi.libraries.upload_data(self, data, folder, **kwargs)

    def upload_from_url(self, url, folder=None, **kwargs):
        return self.gi.libraries.upload_from_url(self, url, folder, **kwargs)

    def upload_from_local(self, path, folder=None, **kwargs):
        return self.gi.libraries.upload_from_local(self, path, folder, **kwargs)

    def upload_from_galaxy_fs(self, paths, folder=None, **kwargs):
        return self.gi.libraries.upload_from_galaxy_fs(
            self, paths, folder, **kwargs
            )

    def create_folder(self, name, description=None, base_folder=None):
        return self.gi.libraries.create_folder(
            self, name, description, base_folder
            )

    def get_folder(self, f_id):
        return self.gi.libraries.get_folder(self, f_id)


class Folder(Wrapper):
    """
    Maps to a folder in a Galaxy library.
    """
    BASE_ATTRS = Wrapper.BASE_ATTRS + ('description', 'item_count')

    def __init__(self, f_dict, container_id, gi=None):
        super(Folder, self).__init__(f_dict, gi=gi)
        if self.id.startswith('F'):  # folder id from library contents
            object.__setattr__(self, 'id', self.id[1:])
        object.__setattr__(self, 'container_id', container_id)

    @property
    def gi_module(self):
        return self.gi.libraries


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
        for k, v in inputs.iteritems():
            if isinstance(v, Dataset):
                inputs[k] = {'src': v.SRC, 'id': v.id}
        out_dict = self.gi.gi.tools.run_tool(history.id, self.id, inputs)
        outputs = [history.get_dataset(_['id']) for _ in out_dict['outputs']]
        if wait:
            self.gi._wait_datasets(outputs, polling_interval=polling_interval)
        return outputs


class Preview(Wrapper):
    """
    Abstract base class for Galaxy entity 'previews'.

    Classes derived from this one model the short summaries returned
    by global getters such as ``/api/libraries``.
    """
    BASE_ATTRS = Wrapper.BASE_ATTRS + ('deleted',)
    __metaclass__ = abc.ABCMeta

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
