"""
A basic object-oriented interface for Galaxy entities.
"""

import abc, collections, json


__all__ = [
    'Wrapper',
    'Tool',
    'Step',
    'InputLink',
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


class Wrapper(object):

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, wrapped, parent=None):
        # http://stackoverflow.com/questions/2827623
        object.__setattr__(self, 'core', lambda: None)
        object.__setattr__(self, 'is_modified', False)
        object.__setattr__(self, 'parent', parent)
        # loads(dumps(x)) is a bit faster than deepcopy and allows type checks
        try:
            if not isinstance(wrapped, collections.Mapping):
                raise TypeError
            dumped = json.dumps(wrapped)
        except (TypeError, ValueError):
            raise TypeError('wrapped object must be a JSON serializable dict')
        setattr(self.core, 'wrapped', json.loads(dumped))

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
            raise KeyError('no property with name "%s"' % name)

    # FIXME: things like self.x[0] = 'y' do NOT call self.__setattr__
    def __setattr__(self, name, value):
        if name not in self.core.wrapped:
            raise KeyError('no property with name "%s"' % name)
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


class Tool(object):

    def __init__(self, step_dict, parent):
        self.step_dict = step_dict.copy()
        self.state = json.loads(self.step_dict['tool_state'])
        self.parent = parent

    @property
    def id(self):
        return self.step_dict['tool_id']

    @property
    def version(self):
        return self.step_dict['tool_version']

    @property
    def errors(self):
        return self.step_dict['tool_errors']

    @property
    def params(self):
        return self.state

    def __getitem__(self, key):
        return json.loads(self.state[key])

    def __setitem__(self, key, value):
        if key not in self.state:
            raise KeyError(key)
        self.state[key] = json.dumps(value)
        self.parent.touch()
        self.sync()

    def sync(self):
        self.step_dict['tool_state'] = json.dumps(self.state)


class Step(Wrapper):

    def __init__(self, step_dict, parent):
        super(Step, self).__init__(step_dict, parent)
        if step_dict['type'] == 'tool':
            setattr(self.core, 'tool', Tool(step_dict, self))

    @property
    def tool(self):
        return self.core.tool


class InputLink(Wrapper):

    def __init__(self, input_dict):
        super(InputLink, self).__init__(input_dict)


class Workflow(Wrapper):

    def __init__(self, wf_dict, id=None, links=None):
        super(Workflow, self).__init__(wf_dict)
        steps = wf_dict['steps']
        setattr(self.core, 'steps',
                [Step(steps[str(i)], self) for i in xrange(len(steps))])
        if id is None:
            super(Workflow, self).touch()
        if links is not None:  # outer keys = unencoded ids, e.g., '99', '100'
            links = [
                InputLink(dict(v.items() + [('id', k)]))
                for k, v in sorted(links.items(), key=lambda t: int(t[0]))
                ]
        setattr(self.core, 'id', id)
        setattr(self.core, 'links', links)

    @property
    def steps(self):
        return self.core.steps

    @property
    def id(self):
        return self.core.id

    @property
    def links(self):
        return self.core.links

    def map_links(self, inputs):
        m = {}
        for link, ds in zip(self.links, inputs):
            m[link.id] = {'id': ds.id, 'src': ds.src}
        return m

    def touch(self):
        super(Workflow, self).touch()
        # forget all Galaxy connections
        setattr(self.core, 'id', None)
        setattr(self.core, 'links', None)

    def __eq__(self, other):
        return self.id == other.id and super(Workflow, self).__eq__(other)


class Dataset(Wrapper):

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, ds_dict, src):
        super(Dataset, self).__init__(ds_dict)
        setattr(self.core, 'src', src)

    @property
    def src(self):
        return self.core.src


class HistoryDatasetAssociation(Dataset):

    def __init__(self, ds_dict):
        super(HistoryDatasetAssociation, self).__init__(ds_dict, 'hda')


class LibraryDatasetDatasetAssociation(Dataset):

    def __init__(self, ds_dict):
        super(LibraryDatasetDatasetAssociation, self).__init__(ds_dict, 'ldda')


class LibraryDataset(Dataset):

    def __init__(self, ds_dict):
        super(LibraryDataset, self).__init__(ds_dict, 'ld')


class DatasetContainer(Wrapper):

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, c_dict, id=None, datasets=None):
        super(DatasetContainer, self).__init__(c_dict)
        if datasets is None:
            datasets = []
        setattr(self.core, 'id', id)
        setattr(self.core, 'datasets', datasets)

    @property
    def id(self):
        return self.core.id

    @property
    def datasets(self):
        return self.core.datasets

    def touch(self):
        super(DatasetContainer, self).touch()
        setattr(self.core, 'id', None)  # forget all Galaxy connections


class History(DatasetContainer):

    DS_TYPE = HistoryDatasetAssociation
    API_MODULE = 'histories'

    def __init__(self, hist_dict, id=None, datasets=None):
        super(History, self).__init__(hist_dict, id=id, datasets=datasets)


class Library(DatasetContainer):

    DS_TYPE = LibraryDataset
    API_MODULE = 'libraries'

    def __init__(self, lib_dict, id=None, datasets=None):
        super(Library, self).__init__(lib_dict, id=id, datasets=datasets)


class Folder(Wrapper):

    def __init__(self, f_dict, library):
        super(Folder, self).__init__(f_dict)
        setattr(self.core, 'library', library)

    @property
    def library(self):
        return self.core.library
