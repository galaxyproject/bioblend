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

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, wrapped, parent=None, id=None):
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
        return self.id is not None

    def unmap(self):
        object.__setattr__(self, 'id', None)

    def clone(self):
        return self.__class__(self.core.wrapped)

    def touch(self):
        object.__setattr__(self, 'is_modified', True)
        if self.parent:
            self.parent.touch()

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

    def to_json(self):
        return json.dumps(self.core.wrapped)

    @classmethod
    def from_json(cls, jdef):
        return cls(json.loads(jdef))

    def __repr__(self):
        return "%s(%r)" % (self.__class__.__name__, self.core.wrapped)


class Step(Wrapper):

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, step_dict, parent):
        super(Step, self).__init__(step_dict, parent=parent)
        if not isinstance(self.tool_state, collections.Mapping):
            object.__setattr__(
                self, 'tool_state', _recursive_loads(self.tool_state)
                )


class DataInput(Step):

    def __init__(self, step_dict, parent):
        if step_dict['type'] != 'data_input':
            raise ValueError('not a data input')
        super(DataInput, self).__init__(step_dict, parent)


class Tool(Step):

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

    def __init__(self, wf_dict, id=None, inputs=None):
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
        return self.__itersteps(DataInput)

    def tools(self):
        return self.__itersteps(Tool)

    def get_input_map(self, datasets):
        m = {}
        for i, ds in zip(self.inputs, datasets):
            m[i] = {'id': ds.id, 'src': ds.SRC}
        return m

    def __itersteps(self, step_type):
        for s in self.steps:
            if isinstance(s, step_type):
                yield s


class Dataset(Wrapper):

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, ds_dict, id):
        super(Dataset, self).__init__(ds_dict, id=id)


class HistoryDatasetAssociation(Dataset):

    SRC = 'hda'

    def __init__(self, ds_dict, id):
        super(HistoryDatasetAssociation, self).__init__(ds_dict, id)


class LibraryDatasetDatasetAssociation(Dataset):

    SRC = 'ldda'

    def __init__(self, ds_dict, id):
        super(LibraryDatasetDatasetAssociation, self).__init__(ds_dict, id)


class LibraryDataset(Dataset):

    SRC = 'ld'

    def __init__(self, ds_dict, id):
        super(LibraryDataset, self).__init__(ds_dict, id)


class DatasetContainer(Wrapper):

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, c_dict, id, dataset_ids=None):
        super(DatasetContainer, self).__init__(c_dict, id=id)
        if dataset_ids is None:
            dataset_ids = []
        object.__setattr__(self, 'dataset_ids', dataset_ids)


class History(DatasetContainer):

    DS_TYPE = HistoryDatasetAssociation
    API_MODULE = 'histories'

    def __init__(self, hist_dict, id, dataset_ids=None):
        super(History, self).__init__(hist_dict, id, dataset_ids=dataset_ids)


class Library(DatasetContainer):

    DS_TYPE = LibraryDataset
    API_MODULE = 'libraries'

    def __init__(self, lib_dict, id, dataset_ids=None, folder_ids=None):
        super(Library, self).__init__(lib_dict, id, dataset_ids=dataset_ids)
        if folder_ids is None:
            folder_ids = []
        object.__setattr__(self, 'folder_ids', folder_ids)


class Folder(Wrapper):

    def __init__(self, f_dict, id):
        if id.startswith('F'):  # folder id from library contents
            id = id[1:]
        super(Folder, self).__init__(f_dict, id=id)
