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
    'WorkflowInfo',
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

    Step dicts should be taken from the JSON dump of a workflow, and
    their parent should be the workflow itself.
    """
    __metaclass__ = abc.ABCMeta

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
    BASE_ATTRS = Step.BASE_ATTRS + ('tool_id', 'tool_version', 'tool_state')

    def __init__(self, step_dict, parent):
        if step_dict['type'] != 'tool':
            raise ValueError('not a tool')
        super(Tool, self).__init__(step_dict, parent)
        if not isinstance(self.tool_state, collections.Mapping):
            object.__setattr__(
                self, 'tool_state', _recursive_loads(self.tool_state)
                )


class WorkflowInfo(Wrapper):
    """
    Workflow data related to a specific Galaxy instance.

    Wraps dictionaries returned by lower level ``show`` calls.
    """
    BASE_ATTRS = Wrapper.BASE_ATTRS + ('inputs', 'published', 'steps', 'tags')

    def __init__(self, wf_info_dict, gi=None):
        super(WorkflowInfo, self).__init__(wf_info_dict, gi=gi)
        for step_dict in self.steps.itervalues():
            try:
                params = step_dict['tool_inputs']
            except KeyError:
                pass
            else:
                step_dict['tool_inputs'] = _recursive_loads(params)
        dag, inv_dag = self._get_dag()
        object.__setattr__(self, '_dag', dag)
        object.__setattr__(self, '_inv_dag', inv_dag)

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
            for i in s['input_steps'].itervalues():
                # force ids to str so they can index the steps dict
                head, tail = str(i['source_step']), str(s['id'])
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

        This can be useful for mapping :class:`Workflow` step ids (0
        to n_steps - 1) to :class:`WorkflowInfo` step ids (actual step
        ids from a Galaxy instance).
        """
        ids = []
        inputs = set(self.inputs)
        assert inputs == set(self.dag) - set(self.inv_dag)
        inv_dag = dict((k, v.copy()) for k, v in self.inv_dag.iteritems())
        while inputs:
            head = inputs.pop()
            ids.append(head)
            for tail in self.dag.get(head, []):
                incoming = inv_dag[tail]
                incoming.remove(head)
                if not incoming:
                    inputs.add(tail)
        return ids


class Workflow(Wrapper):
    """
    Workflows represent ordered sequences of computations on Galaxy.

    A workflow defines a sequence of steps that produce one or more
    results from an input dataset.
    """
    BASE_ATTRS = Wrapper.BASE_ATTRS + ('annotation',)
    POLLING_INTERVAL = 10  # for output state monitoring

    def __init__(self, wf_dict, id=None, wf_info=None, gi=None):
        """
        :type wf_dict: dict
        :param wf_dict: a JSON-deserialized dictionary such as the one
          produced by the download/export Galaxy feature.

        :type id: str
        :param id: the id with which this workflow is registered into
          Galaxy, or None if it's not mapped to an actual Galaxy workflow.

        :type wf_info: :class:`WorkflowInfo`
        :param wf_info: instance-specific info for this workflow, or
          None if it's not mapped to an actual Galaxy workflow.
        """
        super(Workflow, self).__init__(wf_dict, gi=gi)
        # outer keys = unencoded ids, e.g., '99', '100'
        steps = [self._build_step(v, self) for _, v in sorted(
            wf_dict['steps'].items(), key=lambda t: int(t[0])
            )]
        object.__setattr__(self, 'steps', steps)
        object.__setattr__(self, 'id', id)
        object.__setattr__(self, 'info', wf_info)
        # add direct bindings for attributes not available through wf_dict
        if wf_info is not None:
            for a in 'published', 'tags':
                object.__setattr__(self, a, getattr(wf_info, a))
            object.__setattr__(self, 'inputs', sorted(wf_info.inputs, key=int))

    @property
    def gi_module(self):
        return self.gi.workflows

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
    def is_mapped(self):
        return super(Workflow, self).is_mapped and self.info

    def unmap(self):
        super(Workflow, self).unmap()
        object.__setattr__(self, 'wf_info', None)

    @property
    def data_inputs(self):
        """
        Return the list of :class:`DataInput` steps for this workflow.
        """
        return [_ for _ in self.steps if isinstance(_, DataInput)]

    @property
    def tools(self):
        """
        Return the list of :class:`Tool` steps for this workflow.
        """
        return [_ for _ in self.steps if isinstance(_, Tool)]

    def get_input_map(self, datasets):
        """
        Map ``datasets`` to input slots in this workflow.

        :type datasets: :class:`~collections.Iterable` of :class:`Dataset`
        :param datasets: datasets to map to workflow inputs.

        :rtype: dict
        :return: a mapping from input slot ids to datasets in the
          format required by the Galaxy web API.
        """
        if self.inputs is None:
            raise RuntimeError('workflow is not mapped to a Galaxy instance')
        m = {}
        for i, ds in zip(self.inputs, datasets):
            m[i] = {'id': ds.id, 'src': ds.SRC}
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

    def delete(self):
        self.gi.workflows.delete(self.id)
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
    BASE_ATTRS = Dataset.BASE_ATTRS + ('state',)
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
        self.gi.histories.delete(self.id, purge=purge)
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
        self.gi.libraries.delete(self.id)
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
    BASE_ATTRS = Wrapper.BASE_ATTRS + ('published', 'tags')

    def __init__(self, pw_dict, gi=None):
        super(WorkflowPreview, self).__init__(pw_dict, gi=gi)

    @property
    def gi_module(self):
        return self.gi.workflows
