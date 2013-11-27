# pylint: disable=W0622

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
    'DatasetContainer',
    'History',
    'Library',
    'Folder',
    'Dataset',
    'HistoryDatasetAssociation',
    'LibraryDatasetDatasetAssociation',
    'LibraryDataset',
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
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, wrapped, parent=None, id=None):
        """
        :type wrapped: dict
        :param wrapped: JSON serializable dictionary

        :type parent: :class:`Wrapper`
        :param parent: the parent of this wrapper

        :type id: str
        :param id: the id with which this wrapper is registered into
          Galaxy, or None if it's not mapped to a Galaxy entity.
        """
        # http://stackoverflow.com/questions/2827623
        object.__setattr__(self, 'core', lambda: None)
        object.__setattr__(self, 'is_modified', False)
        object.__setattr__(self, 'parent', parent)
        object.__setattr__(self, 'id', id)
        # loads(dumps(x)) is a bit faster than deepcopy and allows type checks
        try:
            if not isinstance(wrapped, collections.Mapping):
                raise TypeError
            dumped = json.dumps(wrapped)
        except (TypeError, ValueError):
            raise TypeError('wrapped object must be a JSON serializable dict')
        setattr(self.core, 'wrapped', json.loads(dumped))

    def is_mapped(self):
        """
        Check whether this wrapper is mapped to an actual Galaxy entity.

        :rtype: bool
        :return: :obj:`True` if this wrapper is mapped
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
        return self.__class__(self.core.wrapped)

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
        return json.dumps(self.core.wrapped)

    @classmethod
    def from_json(cls, jdef):
        """
        Build a new wrapper from a JSON dump.
        """
        return cls(json.loads(jdef))

    def __getattr__(self, name):
        try:
            return self.core.wrapped[name]
        except KeyError:
            raise AttributeError('%r object has no attribute %r' % (
                self.__class__.__name__, name
                ))

    # FIXME: things like self.x[0] = 'y' do NOT call self.__setattr__
    def __setattr__(self, name, value):
        if name not in self.core.wrapped:
            raise AttributeError("can't set attribute")
        else:
            self.core.wrapped[name] = value
            self.touch()

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.core.wrapped)


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
        super(Step, self).__init__(step_dict, parent=parent)
        if not isinstance(self.tool_state, collections.Mapping):
            object.__setattr__(
                self, 'tool_state', _recursive_loads(self.tool_state)
                )


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

    def __init__(self, step_dict, parent):
        if step_dict['type'] != 'tool':
            raise ValueError('not a tool')
        super(Tool, self).__init__(step_dict, parent)


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


class Workflow(Wrapper):
    """
    Workflows represent ordered sequences of computations on Galaxy.

    A workflow defines a sequence of steps that produce one or more
    results from an input dataset.
    """

    def __init__(self, wf_dict, id=None, inputs=None):
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
        super(Workflow, self).__init__(wf_dict, id=id)
        # outer keys = unencoded ids, e.g., '99', '100'
        steps = [_build_step(v, self) for _, v in sorted(
            wf_dict['steps'].items(), key=lambda t: int(t[0])
            )]
        if inputs is not None:
            inputs = sorted(inputs, key=int)
        object.__setattr__(self, 'steps', steps)
        object.__setattr__(self, 'inputs', inputs)

    def is_mapped(self):
        return super(Workflow, self).is_mapped() and self.inputs

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


class Dataset(Wrapper):
    """
    Abstract base class for Galaxy datasets.
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, ds_dict, id, container_id):
        super(Dataset, self).__init__(ds_dict, id=id)
        object.__setattr__(self, 'container_id', container_id)


class HistoryDatasetAssociation(Dataset):
    """
    Maps to a Galaxy ``HistoryDatasetAssociation``.
    """

    SRC = 'hda'

    def __init__(self, ds_dict, id, container_id):
        super(HistoryDatasetAssociation, self).__init__(
            ds_dict, id, container_id
            )


class LibraryDatasetDatasetAssociation(Dataset):
    """
    Maps to a Galaxy ``LibraryDatasetDatasetAssociation``.
    """

    SRC = 'ldda'

    def __init__(self, ds_dict, id, container_id):
        super(LibraryDatasetDatasetAssociation, self).__init__(
            ds_dict, id, container_id
            )


class LibraryDataset(Dataset):
    """
    Maps to a Galaxy ``LibraryDataset``.
    """

    SRC = 'ld'

    def __init__(self, ds_dict, id, container_id):
        super(LibraryDataset, self).__init__(ds_dict, id, container_id)


class DatasetContainer(Wrapper):
    """
    Abstract base class for dataset containers (histories and libraries).
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, c_dict, id, dataset_ids=None):
        """
        :type dataset_ids: list of str
        :param dataset_ids: ids of datasets associated with this container
        """
        super(DatasetContainer, self).__init__(c_dict, id=id)
        if dataset_ids is None:
            dataset_ids = []
        object.__setattr__(self, 'dataset_ids', dataset_ids)


class History(DatasetContainer):
    """
    Maps to a Galaxy history.
    """

    DS_TYPE = HistoryDatasetAssociation
    API_MODULE = 'histories'

    def __init__(self, hist_dict, id, dataset_ids=None):
        super(History, self).__init__(hist_dict, id, dataset_ids=dataset_ids)


class Library(DatasetContainer):
    """
    Maps to a Galaxy library.
    """

    DS_TYPE = LibraryDataset
    API_MODULE = 'libraries'

    def __init__(self, lib_dict, id, dataset_ids=None, folder_ids=None):
        super(Library, self).__init__(lib_dict, id, dataset_ids=dataset_ids)
        if folder_ids is None:
            folder_ids = []
        object.__setattr__(self, 'folder_ids', folder_ids)


class Folder(Wrapper):
    """
    Maps to a folder in a Galaxy library.
    """

    def __init__(self, f_dict, id, container_id):
        if id.startswith('F'):  # folder id from library contents
            id = id[1:]
        super(Folder, self).__init__(f_dict, id=id)
        object.__setattr__(self, 'container_id', container_id)
