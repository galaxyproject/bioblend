# pylint: disable=W0622,E1101

"""
A basic object-oriented interface for Galaxy entities.
"""

import abc, collections, json

from client import ObjHistoryClient

__all__ = [
    'Wrapper',
    'Step',
    'DataInput',
    'Tool',
    'Workflow',
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
    BASE_ATTRS = ('name',)
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, step_dict, parent):
        super(Step, self).__init__(step_dict, parent=parent, gi=parent.gi)


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

class Workflow(Wrapper):
    """
    Workflows represent ordered sequences of computations on Galaxy.

    A workflow defines a sequence of steps that produce one or more
    results from an input dataset.
    """
    BASE_ATTRS = Wrapper.BASE_ATTRS + ('annotation',)

    def __init__(self, wf_dict, id=None, inputs=None, gi=None):
        """
        :type wf_dict: dict
        :param wf_dict: a JSON-deserialized dictionary such as the one
          produced by the download/export Galaxy feature.

        :type id: str
        :param id: the id with which this workflow is registered into
          Galaxy, or None if it's not mapped to an actual Galaxy workflow.

        :type inputs: dict
        :param inputs: the 'inputs' field of the dictionary returned
          by the Galaxy web API for this workflow, or None if it's not
          mapped to an actual Galaxy workflow.  The 'inputs' field is
          in turn a dictionary with the following structure: ``{ID:
          {'label': LABEL, 'value': VALUE}, ...}``.  Currently, only
          the IDs are used.
        """
        super(Workflow, self).__init__(wf_dict, gi=gi)
        # outer keys = unencoded ids, e.g., '99', '100'
        steps = [self._build_step(v, self) for _, v in sorted(
            wf_dict['steps'].items(), key=lambda t: int(t[0])
            )]
        if inputs is not None:
            inputs = sorted(inputs, key=int)
        object.__setattr__(self, 'steps', steps)
        object.__setattr__(self, 'id', id)
        object.__setattr__(self, 'inputs', inputs)

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
        return super(Workflow, self).is_mapped and self.inputs

    def unmap(self):
        super(Workflow, self).unmap()
        object.__setattr__(self, 'inputs', None)

    def data_inputs(self):
        """
        Return the list of :class:`DataInput` steps for this workflow.
        """
        return [_ for _ in self.steps if isinstance(_, DataInput)]

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
        m = {}
        for i, ds in zip(self.inputs, datasets):
            m[i] = {'id': ds.id, 'src': ds.SRC}
        return m

    def import_me(self):
        return self.gi.workflows.import_one(self)

    def preview(self):
        ws = [ _ for _ in self.gi.workflows.get_previews(name=self.name) if _.id == self.id ]
        if len(ws) > 1:
            raise NotImplementedError("Didn't think there could be more than one preview. File a bug report")
        return ws[0] if len(ws) > 0 else None

    def run(self, inputs, history, params=None, import_inputs=False, wait=True):
        outputs, history = self.gi.workflows.run(self, inputs, history, params, import_inputs)
        if wait:
            self.gi.workflows.wait(outputs, history)
        return outputs, history

    def delete(self):
        self.gi.workflows.delete(self)

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

    def get_stream(self, chunk_size=None):
        """
        Open ``dataset`` for reading and return an iterator over its contents.

        :type chunk_size: int
        :param chunk_size: read this amount of bytes at a time
        """
        raise NotImplementedError()

    def peek(self, chunk_size=None):
       return self.get_stream(chunk_size).next()

    def download(self, file_object, chunk_size=None):
        for chunk in self.get_stream(chunk_size=chunk_size):
            file_object.write(chunk)

    def get_contents(self, chunk_size=None):
        return ''.join(self.get_stream(chunk_size=chunk_size))

    def refresh(self):
        """
        Re-fetch the attributes pertaining to this object.

        Returns: self
        """
        raise NotImplementedError()

    def _refresh_imp(self, gi_module):
        fresh = gi_module.get_dataset(self.container_id, self.id)
        self.__init__(fresh.wrapped, self.container_id, self.gi)
        return self

class HistoryDatasetAssociation(Dataset):
    """
    Maps to a Galaxy ``HistoryDatasetAssociation``.
    """
    BASE_ATTRS = Dataset.BASE_ATTRS + ('state',)
    SRC = 'hda'

    def __init__(self, ds_dict, container_id, gi=None):
        super(HistoryDatasetAssociation, self).__init__(ds_dict, container_id, gi=gi)

    def get_stream(self, chunk_size=None):
        return self.gi.histories.get_stream(self, chunk_size)

    def refresh(self):
        return self._refresh_imp(self.gi.histories)

    def wait(self, polling_interval=None):
        ObjHistoryClient.wait(self, polling_interval)

class LibraryDatasetDatasetAssociation(Dataset):
    """
    Maps to a Galaxy ``LibraryDatasetDatasetAssociation``.
    """
    SRC = 'ldda'

    def __init__(self, ds_dict, container_id, gi=None):
        super(LibraryDatasetDatasetAssociation, self).__init__(
            ds_dict, container_id, gi=gi
            )

    def get_stream(self, chunk_size=None):
        return self.gi.libraries.get_stream(self, chunk_size)

    def refresh(self):
        return self._refresh_imp(self.gi.libraries)


class LibraryDataset(Dataset):
    """
    Maps to a Galaxy ``LibraryDataset``.
    """
    SRC = 'ld'

    def __init__(self, ds_dict, container_id, gi=None):
        super(LibraryDataset, self).__init__(ds_dict, container_id, gi=gi)

    def get_stream(self, chunk_size=None):
        return self.gi.libraries.get_stream(self, chunk_size)

    def refresh(self):
        return self._refresh_imp(self.gi.libraries)


class DatasetContainer(Wrapper):
    """
    Abstract base class for dataset containers (histories and libraries).
    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, c_dict, dataset_ids=None, gi=None):
        """
        :type dataset_ids: list of str
        :param dataset_ids: ids of datasets associated with this container
        """
        super(DatasetContainer, self).__init__(c_dict, gi=gi)
        if dataset_ids is None:
            dataset_ids = []
        object.__setattr__(self, 'dataset_ids', dataset_ids)

    @staticmethod
    def _preview(obj, gi_module):
        raise NotImplementedError()
        # TODO: how do I know whether this history has been deleted? Figure it out
        # and fix the deleted= argument below
        hs = [ _ for _ in gi_module.get_previews(name=obj.name, deleted=obj.state) if _.id == obj.id ]
        if len(hs) > 1:
            raise NotImplementedError("Didn't think there could be more than one preview. File a bug report")
        return hs[0] if len(hs) > 0 else None

class History(DatasetContainer):
    """
    Maps to a Galaxy history.
    """
    BASE_ATTRS = DatasetContainer.BASE_ATTRS + ('annotation', 'state_ids')
    DS_TYPE = HistoryDatasetAssociation
    API_MODULE = 'histories'

    def __init__(self, hist_dict, dataset_ids=None, gi=None):
        # XXX: how do we keep this local dataset id list synchronized with the remote contents?
        super(History, self).__init__(hist_dict, dataset_ids=dataset_ids, gi=gi)

    def preview(self):
        return self._preview(self, self.gi.histories)

    def update(self, name=None, annotation=None):
        # TODO: wouldn't it be better if name and annotation were attributes?
        # TODO: do we need to ensure the attributes of `self` are the same as
        # the ones returned by the call to `update` below?
        return self.gi.histories.update(self, name, annotation)

    def delete(self, purge=False):
        self.gi.histories.delete(self, purge)

    def import_dataset(self, lds):
        return self.gi.histories.import_dataset(self, lds)

    def get_dataset(self, ds_id):
        return self.gi.histories.get_dataset(self, ds_id)

    def get_datasets(self):
        return self.gi.histories.get_datasets(self)

class Library(DatasetContainer):
    """
    Maps to a Galaxy library.
    """
    BASE_ATTRS = DatasetContainer.BASE_ATTRS + ('description', 'synopsis')
    DS_TYPE = LibraryDataset
    API_MODULE = 'libraries'

    def __init__(self, lib_dict, dataset_ids=None, folder_ids=None, gi=None):
        super(Library, self).__init__(lib_dict, dataset_ids=dataset_ids, gi=gi)
        if folder_ids is None:
            folder_ids = []
        object.__setattr__(self, 'folder_ids', folder_ids)

    def preview(self):
        return self._preview(self, self.gi.libraries)

    def delete(self):
        self.gi.libraries.delete(self)

    def upload_data(self, data, folder=None, **kwargs):
        return self.gi.libraries.upload_data(self, data, folder, **kwargs)

    def upload_from_url(self, url, folder=None, **kwargs):
        return self.gi.libraries.upload_from_url(self, url, folder, **kwargs)

    def upload_from_local(self, path, folder=None, **kwargs):
        return self.gi.libraries.upload_from_local(self, path, folder, **kwargs)

    def upload_from_galaxy_fs(self, paths, folder=None, **kwargs):
        return self.gi.libraries.upload_from_galaxy_fs(self, paths, folder, **kwargs)

    def get_dataset(self, ds_id):
        return self.gi.libraries.get_dataset(self, ds_id)

    def get_datasets(self):
        return self.gi.libraries.get_datasets(self)

    def create_folder(self, name, description=None, base_folder=None):
        return self.gi.libraries.create_folder(self, name, description, base_folder)

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


class HistoryPreview(Preview):
    """
    Models Galaxy history 'previews'.

    Instances of this class wrap dictionaries obtained by getting
    ``/api/histories`` from Galaxy.
    """
    def __init__(self, pw_dict, gi=None):
        super(HistoryPreview, self).__init__(pw_dict, gi=gi)


class WorkflowPreview(Preview):
    """
    Models Galaxy workflow 'previews'.

    Instances of this class wrap dictionaries obtained by getting
    ``/api/workflows`` from Galaxy.
    """
    def __init__(self, pw_dict, gi=None):
        super(WorkflowPreview, self).__init__(pw_dict, gi=gi)
