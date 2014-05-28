# pylint: disable=W0622,E1101

"""
A basic object-oriented interface for Galaxy entities.
"""

import abc, collections, json


__all__ = [
    'Wrapper',
    'Step',
    'DataInput',
    'Tool',
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
    can refer to either an input dataset (:class:`DataInput`) or a
    computational tool (:class:`Tool`).
    """
    __metaclass__ = abc.ABCMeta
    BASE_ATTRS = Wrapper.BASE_ATTRS + ('input_steps',)

    @abc.abstractmethod
    def __init__(self, step_dict, parent):
        super(Step, self).__init__(step_dict, parent=parent, gi=parent.gi)

    @property
    def gi_module(self):
        return self.gi.workflows


class DataInput(Step):
    """
    DataInputs model input datasets for Galaxy tools.
    """
    def __init__(self, step_dict, parent):
        if step_dict['type'] != 'data_input':
            raise ValueError('not a data input')
        super(DataInput, self).__init__(step_dict, parent)


class Tool(Step):
    """
    Tools model Galaxy tools.
    """
    BASE_ATTRS = Step.BASE_ATTRS + ('tool_id', 'tool_inputs', 'tool_version')

    def __init__(self, step_dict, parent):
        if step_dict['type'] != 'tool':
            raise ValueError('not a tool')
        super(Tool, self).__init__(step_dict, parent)
        if self.tool_inputs:
            for k, v in self.tool_inputs.iteritems():
                self.tool_inputs[k] = json.loads(v)


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
            if isinstance(step, Tool) and not step.tool_inputs:
                missing_ids.append(k)
        input_labels_to_ids = {}
        for id_, d in self.inputs.iteritems():
            input_labels_to_ids.setdefault(d['label'], set()).add(id_)
        tool_labels_to_ids = {}
        for s in self.steps.itervalues():
            if isinstance(s, Tool):
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

          {'a': {'c'}, 'b': {'c'}, 'c': {'d', 'e', 'f'}}

        and by (inverse)::

          {'c': {'a', 'b'}, 'd': {'c'}, 'e': {'c'}, 'f': {'c'}}
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
        if stype == 'data_input':
            return DataInput(step_dict, parent)
        elif stype == 'tool':
            return Tool(step_dict, parent)
        else:
            raise ValueError('unknown step type: %r' % (stype,))

    @property
    def data_input_ids(self):
        """
        Return the list of :class:`DataInput` steps for this workflow.
        """
        return set(id_ for id_, s in self.steps.iteritems()
                   if isinstance(s, DataInput))

    @property
    def tool_ids(self):
        """
        Return the list of :class:`Tool` steps for this workflow.
        """
        return set(id_ for id_, s in self.steps.iteritems()
                   if isinstance(s, Tool))

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

    def run(self, inputs, history, params=None, import_inputs=False,
            replacement_params=None, wait=False,
            polling_interval=POLLING_INTERVAL, break_on_error=True):
        outputs, history = self.gi.workflows.run(
            self, inputs, history, params=params, import_inputs=import_inputs,
            replacement_params=replacement_params
            )
        if wait:
            self.gi.histories.wait(outputs, polling_interval=polling_interval,
                                   break_on_error=break_on_error)
        return outputs, history

    def export(self):
        return self.gi.workflows.export(self.id)

    def delete(self):
        self.gi.workflows.delete(id_=self.id)
        self.unmap()


class Dataset(Wrapper):
    """
    Abstract base class for Galaxy datasets.
    """
    BASE_ATTRS = Wrapper.BASE_ATTRS + ('data_type', 'file_name', 'file_size')
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, ds_dict, container_id, gi=None):
        super(Dataset, self).__init__(ds_dict, gi=gi)
        object.__setattr__(self, 'container_id', container_id)

    @abc.abstractmethod
    def get_stream(self, chunk_size=None):
        """
        Open dataset for reading and return an iterator over its contents.

        :type chunk_size: int
        :param chunk_size: read this amount of bytes at a time
        """
        pass

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
        fresh = self.gi_module.get_dataset(self.container_id, self.id)
        self.__init__(fresh.wrapped, self.container_id, self.gi)
        return self


class HistoryDatasetAssociation(Dataset):
    """
    Maps to a Galaxy ``HistoryDatasetAssociation``.
    """
    BASE_ATTRS = Dataset.BASE_ATTRS + ('state', 'deleted')
    SRC = 'hda'
    POLLING_INTERVAL = 1  # for state monitoring

    def __init__(self, ds_dict, container_id, gi=None):
        super(HistoryDatasetAssociation, self).__init__(
            ds_dict, container_id, gi=gi
            )

    @property
    def gi_module(self):
        return self.gi.histories

    def get_stream(self, chunk_size=None):
        return self.gi.histories.get_stream(self, chunk_size=chunk_size)

    def wait(self, polling_interval=POLLING_INTERVAL, break_on_error=True):
        self.gi.histories.wait([self], polling_interval=polling_interval,
                               break_on_error=break_on_error)


class LibRelatedDataset(Dataset):

    def __init__(self, ds_dict, container_id, gi=None):
        super(LibRelatedDataset, self).__init__(ds_dict, container_id, gi=gi)

    @property
    def gi_module(self):
        return self.gi.libraries

    def get_stream(self, chunk_size=None):
        return self.gi.libraries.get_stream(self, chunk_size=chunk_size)


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
        # TODO: wouldn't it be better if name and annotation were attributes?
        # TODO: do we need to ensure the attributes of `self` are the same as
        # the ones returned by the call to `update` below?
        return self.gi.histories.update(self, name, annotation)

    def delete(self, purge=False):
        self.gi.histories.delete(id_=self.id, purge=purge)
        self.unmap()

    def import_dataset(self, lds):
        return self.gi.histories.import_dataset(self, lds)

    def get_dataset(self, ds_id):
        return self.gi.histories.get_dataset(self, ds_id)

    def get_datasets(self, name=None):
        return self.gi.histories.get_datasets(self, name=name)


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

    def get_dataset(self, ds_id):
        return self.gi.libraries.get_dataset(self, ds_id)

    def get_datasets(self, name=None):
        return self.gi.libraries.get_datasets(self, name=name)

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
