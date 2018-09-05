# pylint: disable=C0103,E1101
import json
import os
import shutil
import socket
import sys
import tarfile
import tempfile
import uuid
from ssl import SSLError

import six
from six.moves.urllib.error import URLError
from six.moves.urllib.request import urlopen

import bioblend
import bioblend.galaxy.objects.galaxy_instance as galaxy_instance
import bioblend.galaxy.objects.wrappers as wrappers
from bioblend import ConnectionError
from bioblend.galaxy import dataset_collections
from . import test_util
from .test_util import unittest

bioblend.set_stream_logger('test', level='INFO')
socket.setdefaulttimeout(10.0)
SAMPLE_FN = test_util.get_abspath(os.path.join('data', 'paste_columns.ga'))
SAMPLE_WF_COLL_FN = test_util.get_abspath(os.path.join('data', 'paste_columns_collections.ga'))
FOO_DATA = 'foo\nbar\n'
FOO_DATA_2 = 'foo2\nbar2\n'
SAMPLE_WF_DICT = {
    'deleted': False,
    'id': '9005c5112febe774',
    'inputs': {
        '571': {'label': 'Input Dataset', 'value': ''},
        '572': {'label': 'Input Dataset', 'value': ''},
    },
    'model_class': 'StoredWorkflow',
    'name': 'paste_columns',
    'published': False,
    'steps': {
        '571': {
            'id': 571,
            'input_steps': {},
            'tool_id': None,
            'tool_inputs': {'name': 'Input Dataset'},
            'tool_version': None,
            'type': 'data_input',
        },
        '572': {
            'id': 572,
            'input_steps': {},
            'tool_id': None,
            'tool_inputs': {'name': 'Input Dataset'},
            'tool_version': None,
            'type': 'data_input',
        },
        '573': {
            'id': 573,
            'input_steps': {
                'input1': {'source_step': 571, 'step_output': 'output'},
                'input2': {'source_step': 572, 'step_output': 'output'},
            },
            'tool_id': 'Paste1',
            'tool_inputs': {
                'delimiter': '"T"',
                'input1': 'null',
                'input2': 'null',
            },
            'tool_version': '1.0.0',
            'type': 'tool',
        }
    },
    'tags': [],
    'url': '/api/workflows/9005c5112febe774',
}


def is_reachable(url):
    res = None
    try:
        res = urlopen(url, timeout=5)
    except (SSLError, URLError, socket.timeout):
        return False
    if res is not None:
        res.close()
    return True


def upload_from_fs(lib, bnames, **kwargs):
    tempdir = tempfile.mkdtemp(prefix='bioblend_test_')
    try:
        fnames = [os.path.join(tempdir, _) for _ in bnames]
        for fn in fnames:
            with open(fn, 'w') as f:
                f.write(FOO_DATA)
        dss = lib.upload_from_galaxy_fs(fnames, **kwargs)
    finally:
        shutil.rmtree(tempdir)
    return dss, fnames


class MockWrapper(wrappers.Wrapper):
    BASE_ATTRS = frozenset(['a', 'b'])

    def __init__(self, *args, **kwargs):
        super(MockWrapper, self).__init__(*args, **kwargs)

    @property
    def gi_module(self):
        return super(MockWrapper, self).gi_module()


class TestWrapper(unittest.TestCase):

    def setUp(self):
        self.d = {'a': 1, 'b': [2, 3], 'c': {'x': 4}}
        self.assertRaises(TypeError, wrappers.Wrapper, self.d)
        self.w = MockWrapper(self.d)

    def test_initialize(self):
        for k in MockWrapper.BASE_ATTRS:
            self.assertEqual(getattr(self.w, k), self.d[k])
        self.w.a = 222
        self.w.b[0] = 222
        self.assertEqual(self.w.a, 222)
        self.assertEqual(self.w.b[0], 222)
        self.assertEqual(self.d['a'], 1)
        self.assertEqual(self.d['b'][0], 2)
        self.assertRaises(AttributeError, getattr, self.w, 'foo')
        self.assertRaises(AttributeError, setattr, self.w, 'foo', 0)

    def test_taint(self):
        self.assertFalse(self.w.is_modified)
        self.w.a = 111  # pylint: disable=W0201
        self.assertTrue(self.w.is_modified)

    def test_serialize(self):
        w = MockWrapper.from_json(self.w.to_json())
        self.assertEqual(w.wrapped, self.w.wrapped)

    def test_clone(self):
        w = self.w.clone()
        self.assertEqual(w.wrapped, self.w.wrapped)
        w.b[0] = 111
        self.assertEqual(self.w.b[0], 2)

    def test_kwargs(self):
        parent = MockWrapper({'a': 10})
        w = MockWrapper(self.d, parent=parent)
        self.assertIs(w.parent, parent)
        self.assertRaises(AttributeError, setattr, w, 'parent', 0)


class TestWorkflow(unittest.TestCase):

    def setUp(self):
        self.wf = wrappers.Workflow(SAMPLE_WF_DICT)

    def test_initialize(self):
        self.assertEqual(self.wf.id, '9005c5112febe774')
        self.assertEqual(self.wf.name, 'paste_columns')
        self.assertEqual(self.wf.deleted, False)
        self.assertEqual(self.wf.published, False)
        self.assertEqual(self.wf.tags, [])
        self.assertEqual(
            self.wf.input_labels_to_ids, {'Input Dataset': set(['571', '572'])})
        self.assertEqual(self.wf.tool_labels_to_ids, {'Paste1': set(['573'])})
        self.assertEqual(self.wf.data_input_ids, set(['571', '572']))
        self.assertEqual(self.wf.source_ids, set(['571', '572']))
        self.assertEqual(self.wf.sink_ids, set(['573']))

    def test_dag(self):
        inv_dag = {}
        for h, tails in six.iteritems(self.wf.dag):
            for t in tails:
                inv_dag.setdefault(str(t), set()).add(h)
        self.assertEqual(self.wf.inv_dag, inv_dag)
        heads = set(self.wf.dag)
        self.assertEqual(heads, set.union(*self.wf.inv_dag.values()))
        tails = set(self.wf.inv_dag)
        self.assertEqual(tails, set.union(*self.wf.dag.values()))
        ids = self.wf.sorted_step_ids()
        self.assertEqual(set(ids), heads | tails)
        for h, tails in six.iteritems(self.wf.dag):
            for t in tails:
                self.assertLess(ids.index(h), ids.index(t))

    def test_steps(self):
        steps = SAMPLE_WF_DICT['steps']
        for sid, s in six.iteritems(self.wf.steps):
            self.assertIsInstance(s, wrappers.Step)
            self.assertEqual(s.id, sid)
            self.assertIn(sid, steps)
            self.assertIs(s.parent, self.wf)
        self.assertEqual(self.wf.data_input_ids, set(['571', '572']))
        self.assertEqual(self.wf.tool_ids, set(['573']))

    def test_taint(self):
        self.assertFalse(self.wf.is_modified)
        self.wf.steps['571'].tool_id = 'foo'
        self.assertTrue(self.wf.is_modified)

    def test_input_map(self):
        class DummyLD(object):
            SRC = 'ld'

            def __init__(self, id_):
                self.id = id_

        label = 'Input Dataset'
        self.assertEqual(self.wf.input_labels, set([label]))
        input_map = self.wf.convert_input_map(
            {label: [DummyLD('a'), DummyLD('b')]})
        # {'571': {'id': 'a', 'src': 'ld'}, '572': {'id': 'b', 'src': 'ld'}}
        # OR
        # {'571': {'id': 'b', 'src': 'ld'}, '572': {'id': 'a', 'src': 'ld'}}
        self.assertEqual(set(input_map), set(['571', '572']))
        for d in six.itervalues(input_map):
            self.assertEqual(set(d), set(['id', 'src']))
            self.assertEqual(d['src'], 'ld')
            self.assertIn(d['id'], 'ab')


@test_util.skip_unless_galaxy()
class GalaxyObjectsTestBase(unittest.TestCase):

    def setUp(self):
        galaxy_key = os.environ['BIOBLEND_GALAXY_API_KEY']
        galaxy_url = os.environ['BIOBLEND_GALAXY_URL']
        self.gi = galaxy_instance.GalaxyInstance(galaxy_url, galaxy_key)


class TestGalaxyInstance(GalaxyObjectsTestBase):

    def test_library(self):
        name = 'test_%s' % uuid.uuid4().hex
        description, synopsis = 'D', 'S'
        lib = self.gi.libraries.create(
            name, description=description, synopsis=synopsis)
        self.assertEqual(lib.name, name)
        self.assertEqual(lib.description, description)
        self.assertEqual(lib.synopsis, synopsis)
        self.assertEqual(len(lib.content_infos), 1)  # root folder
        self.assertEqual(len(lib.folder_ids), 1)
        self.assertEqual(len(lib.dataset_ids), 0)
        self.assertIn(lib.id, [_.id for _ in self.gi.libraries.list()])
        lib.delete()
        self.assertFalse(lib.is_mapped)

    def test_workflow_from_str(self):
        with open(SAMPLE_FN) as f:
            wf = self.gi.workflows.import_new(f.read())
        self._check_and_del_workflow(wf)

    def test_workflow_collections_from_str(self):
        with open(SAMPLE_WF_COLL_FN) as f:
            wf = self.gi.workflows.import_new(f.read())
        self._check_and_del_workflow(wf)

    def test_workflow_from_dict(self):
        with open(SAMPLE_FN) as f:
            wf = self.gi.workflows.import_new(json.load(f))
        self._check_and_del_workflow(wf)

    def test_workflow_publish_from_dict(self):
        with open(SAMPLE_FN) as f:
            wf = self.gi.workflows.import_new(json.load(f), publish=True)
        self._check_and_del_workflow(wf, check_is_public=True)

    def test_workflow_missing_tools(self):
        with open(SAMPLE_FN) as f:
            wf_dump = json.load(f)
        wf_info = self.gi.gi.workflows.import_workflow_dict(wf_dump)
        wf_dict = self.gi.gi.workflows.show_workflow(wf_info['id'])
        for id_, step in six.iteritems(wf_dict['steps']):
            if step['type'] == 'tool':
                for k in 'tool_inputs', 'tool_version':
                    wf_dict['steps'][id_][k] = None
        wf = wrappers.Workflow(wf_dict, gi=self.gi)
        self.assertFalse(wf.is_runnable)
        self.assertRaises(RuntimeError, wf.run)
        wf.delete()

    def test_workflow_export(self):
        with open(SAMPLE_FN) as f:
            wf1 = self.gi.workflows.import_new(f.read())
        wf2 = self.gi.workflows.import_new(wf1.export())
        self.assertNotEqual(wf1.id, wf2.id)
        for wf in wf1, wf2:
            self._check_and_del_workflow(wf)

    def _check_and_del_workflow(self, wf, check_is_public=False):
        # Galaxy appends additional text to imported workflow names
        self.assertTrue(wf.name.startswith('paste_columns'))
        self.assertEqual(len(wf.steps), 3)
        for step_id, step in six.iteritems(wf.steps):
            self.assertIsInstance(step, wrappers.Step)
            self.assertEqual(step_id, step.id)
            self.assertIsInstance(step.tool_inputs, dict)
            if step.type == 'tool':
                self.assertIsNotNone(step.tool_id)
                self.assertIsNotNone(step.tool_version)
                self.assertIsInstance(step.input_steps, dict)
            elif step.type in ('data_collection_input', 'data_input'):
                self.assertIsNone(step.tool_id)
                self.assertIsNone(step.tool_version)
                self.assertEqual(step.input_steps, {})
        wf_ids = set(_.id for _ in self.gi.workflows.list())
        self.assertIn(wf.id, wf_ids)
        if check_is_public:
            self.assertTrue(wf.published)
        wf.delete()

    # not very accurate:
    #   * we can't publish a wf from the API
    #   * we can't directly get another user's wf
    def test_workflow_from_shared(self):
        all_prevs = dict(
            (_.id, _) for _ in self.gi.workflows.get_previews(published=True)
        )
        pub_only_ids = set(all_prevs).difference(
            _.id for _ in self.gi.workflows.get_previews())
        if pub_only_ids:
            wf_id = pub_only_ids.pop()
            imported = self.gi.workflows.import_shared(wf_id)
            self.assertIsInstance(imported, wrappers.Workflow)
            imported.delete()
        else:
            self.skipTest('no published workflows, manually publish a workflow to run this test')

    def test_get_libraries(self):
        self._test_multi_get('library')

    def test_get_histories(self):
        self._test_multi_get('history')

    def test_get_workflows(self):
        self._test_multi_get('workflow')

    def _normalized_functions(self, obj_type):
        if obj_type == 'library':
            create = self.gi.libraries.create
            get_objs = self.gi.libraries.list
            get_prevs = self.gi.libraries.get_previews
            del_kwargs = {}
        elif obj_type == 'history':
            create = self.gi.histories.create
            get_objs = self.gi.histories.list
            get_prevs = self.gi.histories.get_previews
            del_kwargs = {'purge': True}
        elif obj_type == 'workflow':
            def create(name):
                with open(SAMPLE_FN) as f:
                    d = json.load(f)
                d['name'] = name
                return self.gi.workflows.import_new(d)

            get_objs = self.gi.workflows.list
            get_prevs = self.gi.workflows.get_previews
            del_kwargs = {}
        return create, get_objs, get_prevs, del_kwargs

    def _test_multi_get(self, obj_type):
        create, get_objs, get_prevs, del_kwargs = self._normalized_functions(
            obj_type)

        def ids(seq):
            return set(_.id for _ in seq)

        names = ['test_%s' % uuid.uuid4().hex for _ in range(2)]
        objs = []
        try:
            objs = [create(_) for _ in names]
            self.assertLessEqual(ids(objs), ids(get_objs()))
            if obj_type != 'workflow':
                filtered = get_objs(name=names[0])
                self.assertEqual(len(filtered), 1)
                self.assertEqual(filtered[0].id, objs[0].id)
                del_id = objs[-1].id
                objs.pop().delete(**del_kwargs)
                self.assertIn(del_id, ids(get_prevs(deleted=True)))
            else:
                # Galaxy appends info strings to imported workflow names
                prev = get_prevs()[0]
                filtered = get_objs(name=prev.name)
                self.assertEqual(len(filtered), 1)
                self.assertEqual(filtered[0].id, prev.id)
        finally:
            for o in objs:
                o.delete(**del_kwargs)

    def test_delete_libraries_by_name(self):
        self._test_delete_by_name('library')

    def test_delete_histories_by_name(self):
        self._test_delete_by_name('history')

    def test_delete_workflows_by_name(self):
        self._test_delete_by_name('workflow')

    def _test_delete_by_name(self, obj_type):
        create, _, get_prevs, del_kwargs = self._normalized_functions(
            obj_type)
        name = 'test_%s' % uuid.uuid4().hex
        objs = [create(name) for _ in range(2)]  # noqa: F812
        final_name = objs[0].name
        prevs = [_ for _ in get_prevs(name=final_name) if not _.deleted]
        self.assertEqual(len(prevs), len(objs))
        del_kwargs['name'] = final_name
        objs[0].gi_module.delete(**del_kwargs)
        prevs = [_ for _ in get_prevs(name=final_name) if not _.deleted]
        self.assertEqual(len(prevs), 0)


class TestLibrary(GalaxyObjectsTestBase):
    # just something that can be expected to be always up
    DS_URL = 'https://tools.ietf.org/rfc/rfc1866.txt'

    def setUp(self):
        super(TestLibrary, self).setUp()
        self.lib = self.gi.libraries.create('test_%s' % uuid.uuid4().hex)

    def tearDown(self):
        self.lib.delete()

    def test_root_folder(self):
        r = self.lib.root_folder
        self.assertIsNone(r.parent)

    def test_folder(self):
        name, desc = 'test_%s' % uuid.uuid4().hex, 'D'
        folder = self.lib.create_folder(name, description=desc)
        self.assertEqual(folder.name, name)
        self.assertEqual(folder.description, desc)
        self.assertIs(folder.container, self.lib)
        self.assertEqual(folder.parent.id, self.lib.root_folder.id)
        self.assertEqual(len(self.lib.content_infos), 2)
        self.assertEqual(len(self.lib.folder_ids), 2)
        self.assertIn(folder.id, self.lib.folder_ids)
        retrieved = self.lib.get_folder(folder.id)
        self.assertEqual(folder.id, retrieved.id)

    def _check_datasets(self, dss):
        self.assertEqual(len(dss), len(self.lib.dataset_ids))
        self.assertEqual(set(_.id for _ in dss), set(self.lib.dataset_ids))
        for ds in dss:
            self.assertIs(ds.container, self.lib)

    def test_dataset(self):
        folder = self.lib.create_folder('test_%s' % uuid.uuid4().hex)
        ds = self.lib.upload_data(FOO_DATA, folder=folder)
        self.assertEqual(len(self.lib.content_infos), 3)
        self.assertEqual(len(self.lib.folder_ids), 2)
        self._check_datasets([ds])

    def test_dataset_from_url(self):
        if is_reachable(self.DS_URL):
            ds = self.lib.upload_from_url(self.DS_URL)
            self._check_datasets([ds])
        else:
            self.skipTest('%s not reachable' % self.DS_URL)

    def test_dataset_from_local(self):
        with tempfile.NamedTemporaryFile(mode='w', prefix='bioblend_test_') as f:
            f.write(FOO_DATA)
            f.flush()
            ds = self.lib.upload_from_local(f.name)
        self._check_datasets([ds])

    def test_datasets_from_fs(self):
        bnames = ['f%d.txt' % i for i in range(2)]
        dss, fnames = upload_from_fs(self.lib, bnames)
        self._check_datasets(dss)
        dss, fnames = upload_from_fs(
            self.lib, bnames, link_data_only='link_to_files')
        for ds, fn in zip(dss, fnames):
            self.assertEqual(ds.file_name, fn)

    def test_copy_from_dataset(self):
        hist = self.gi.histories.create('test_%s' % uuid.uuid4().hex)
        try:
            hda = hist.paste_content(FOO_DATA)
            ds = self.lib.copy_from_dataset(hda)
        finally:
            hist.delete(purge=True)
        self._check_datasets([ds])

    def test_get_dataset(self):
        ds = self.lib.upload_data(FOO_DATA)
        retrieved = self.lib.get_dataset(ds.id)
        self.assertEqual(ds.id, retrieved.id)

    def test_get_datasets(self):
        bnames = ['f%d.txt' % _ for _ in range(2)]
        dss, _ = upload_from_fs(self.lib, bnames)
        retrieved = self.lib.get_datasets()
        self.assertEqual(len(dss), len(retrieved))
        self.assertEqual(set(_.id for _ in dss), set(_.id for _ in retrieved))
        name = '/%s' % bnames[0]
        selected = self.lib.get_datasets(name=name)
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0].name, bnames[0])


class TestLDContents(GalaxyObjectsTestBase):

    def setUp(self):
        super(TestLDContents, self).setUp()
        self.lib = self.gi.libraries.create('test_%s' % uuid.uuid4().hex)
        self.ds = self.lib.upload_data(FOO_DATA)
        self.ds.wait()

    def tearDown(self):
        self.lib.delete()

    def test_dataset_get_stream(self):
        for idx, c in enumerate(self.ds.get_stream(chunk_size=1)):
            self.assertEqual(six.b(FOO_DATA[idx]), c)

    def test_dataset_peek(self):
        fetched_data = self.ds.peek(chunk_size=4)
        self.assertEqual(six.b(FOO_DATA[0:4]), fetched_data)

    def test_dataset_download(self):
        with tempfile.TemporaryFile() as f:
            self.ds.download(f)
            f.seek(0)
            self.assertEqual(six.b(FOO_DATA), f.read())

    def test_dataset_get_contents(self):
        self.assertEqual(six.b(FOO_DATA), self.ds.get_contents())

    def test_dataset_delete(self):
        self.ds.delete()
        # Cannot test this yet because the 'deleted' attribute is not exported
        # by the API at the moment
        # self.assertTrue(self.ds.deleted)

    @test_util.skip_unless_galaxy('release_17.09')
    def test_dataset_update(self):
        new_name = 'test_%s' % uuid.uuid4().hex
        new_misc_info = 'Annotation for %s' % new_name
        new_genome_build = 'hg19'
        updated_ldda = self.ds.update(name=new_name, misc_info=new_misc_info, genome_build=new_genome_build)
        self.assertEqual(self.ds.id, updated_ldda.id)
        self.assertEqual(self.ds.name, new_name)
        self.assertEqual(self.ds.misc_info, new_misc_info)
        self.assertEqual(self.ds.genome_build, new_genome_build)


class TestHistory(GalaxyObjectsTestBase):

    def setUp(self):
        super(TestHistory, self).setUp()
        self.hist = self.gi.histories.create('test_%s' % uuid.uuid4().hex)

    def tearDown(self):
        self.hist.delete(purge=True)

    def test_create_delete(self):
        name = 'test_%s' % uuid.uuid4().hex
        hist = self.gi.histories.create(name)
        self.assertEqual(hist.name, name)
        hist_id = hist.id
        self.assertIn(hist_id, [_.id for _ in self.gi.histories.list()])
        hist.delete(purge=True)
        self.assertFalse(hist.is_mapped)
        try:
            h = self.gi.histories.get(hist_id)
            self.assertTrue(h.deleted)
        except ConnectionError:
            # Galaxy up to release_2015.01.13 gives a ConnectionError
            pass

    def _check_dataset(self, hda):
        self.assertIsInstance(hda, wrappers.HistoryDatasetAssociation)
        self.assertIs(hda.container, self.hist)
        self.assertEqual(len(self.hist.dataset_ids), 1)
        self.assertEqual(self.hist.dataset_ids[0], hda.id)

    def test_import_dataset(self):
        lib = self.gi.libraries.create('test_%s' % uuid.uuid4().hex)
        lds = lib.upload_data(FOO_DATA)
        self.assertEqual(len(self.hist.dataset_ids), 0)
        hda = self.hist.import_dataset(lds)
        lib.delete()
        self._check_dataset(hda)

    def test_upload_file(self):
        with tempfile.NamedTemporaryFile(mode='w', prefix='bioblend_test_') as f:
            f.write(FOO_DATA)
            f.flush()
            hda = self.hist.upload_file(f.name)
        self._check_dataset(hda)

    def test_paste_content(self):
        hda = self.hist.paste_content(FOO_DATA)
        self._check_dataset(hda)

    def test_get_dataset(self):
        hda = self.hist.paste_content(FOO_DATA)
        retrieved = self.hist.get_dataset(hda.id)
        self.assertEqual(hda.id, retrieved.id)

    def test_get_datasets(self):
        bnames = ['f%d.txt' % _ for _ in range(2)]
        lib = self.gi.libraries.create('test_%s' % uuid.uuid4().hex)
        lds = upload_from_fs(lib, bnames)[0]
        hdas = [self.hist.import_dataset(_) for _ in lds]
        lib.delete()
        retrieved = self.hist.get_datasets()
        self.assertEqual(len(hdas), len(retrieved))
        self.assertEqual(set(_.id for _ in hdas), set(_.id for _ in retrieved))
        selected = self.hist.get_datasets(name=bnames[0])
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0].name, bnames[0])

    def test_export_and_download(self):
        jeha_id = self.hist.export(wait=True)
        self.assertTrue(jeha_id)
        tempdir = tempfile.mkdtemp(prefix='bioblend_test_')
        temp_fn = os.path.join(tempdir, 'export.tar.gz')
        try:
            with open(temp_fn, 'wb') as fo:
                self.hist.download(jeha_id, fo)
            self.assertTrue(tarfile.is_tarfile(temp_fn))
        finally:
            shutil.rmtree(tempdir)

    def test_update(self):
        new_name = 'test_%s' % uuid.uuid4().hex
        new_annotation = 'Annotation for %s' % new_name
        new_tags = ['tag1', 'tag2']
        updated_hist = self.hist.update(name=new_name, annotation=new_annotation, tags=new_tags)
        self.assertEqual(self.hist.id, updated_hist.id)
        self.assertEqual(self.hist.name, new_name)
        self.assertEqual(self.hist.annotation, new_annotation)
        self.assertEqual(self.hist.tags, new_tags)
        updated_hist = self.hist.update(published=True)
        self.assertEqual(self.hist.id, updated_hist.id)
        self.assertTrue(self.hist.published)

    def test_create_dataset_collection(self):
        self._create_collection_description()
        hdca = self.hist.create_dataset_collection(self.collection_description)
        self.assertIsInstance(hdca, wrappers.HistoryDatasetCollectionAssociation)
        self.assertEqual(hdca.collection_type, 'list')
        self.assertIs(hdca.container, self.hist)
        self.assertEqual(len(hdca.elements), 2)
        self.assertEqual(self.dataset1.id, hdca.elements[0]['object']['id'])
        self.assertEqual(self.dataset2.id, hdca.elements[1]['object']['id'])

    def test_delete_dataset_collection(self):
        self._create_collection_description()
        hdca = self.hist.create_dataset_collection(self.collection_description)
        hdca.delete()
        self.assertTrue(hdca.deleted)

    def _create_collection_description(self):
        self.dataset1 = self.hist.paste_content(FOO_DATA)
        self.dataset2 = self.hist.paste_content(FOO_DATA_2)
        self.collection_description = dataset_collections.CollectionDescription(
            name="MyDatasetList",
            elements=[
                dataset_collections.HistoryDatasetElement(name="sample1", id=self.dataset1.id),
                dataset_collections.HistoryDatasetElement(name="sample2", id=self.dataset2.id),
            ]
        )


class TestHDAContents(GalaxyObjectsTestBase):

    def setUp(self):
        super(TestHDAContents, self).setUp()
        self.hist = self.gi.histories.create('test_%s' % uuid.uuid4().hex)
        self.ds = self.hist.paste_content(FOO_DATA)
        self.ds.wait()

    def tearDown(self):
        self.hist.delete(purge=True)

    def test_dataset_get_stream(self):
        for idx, c in enumerate(self.ds.get_stream(chunk_size=1)):
            self.assertEqual(six.b(FOO_DATA[idx]), c)

    def test_dataset_peek(self):
        fetched_data = self.ds.peek(chunk_size=4)
        self.assertEqual(six.b(FOO_DATA[0:4]), fetched_data)

    def test_dataset_download(self):
        with tempfile.TemporaryFile() as f:
            self.ds.download(f)
            f.seek(0)
            self.assertEqual(six.b(FOO_DATA), f.read())

    def test_dataset_get_contents(self):
        self.assertEqual(six.b(FOO_DATA), self.ds.get_contents())

    def test_dataset_update(self):
        new_name = 'test_%s' % uuid.uuid4().hex
        new_annotation = 'Annotation for %s' % new_name
        new_genome_build = 'hg19'
        updated_hda = self.ds.update(name=new_name, annotation=new_annotation, genome_build=new_genome_build)
        self.assertEqual(self.ds.id, updated_hda.id)
        self.assertEqual(self.ds.name, new_name)
        self.assertEqual(self.ds.annotation, new_annotation)
        self.assertEqual(self.ds.genome_build, new_genome_build)

    def test_dataset_delete(self):
        self.ds.delete()
        self.assertTrue(self.ds.deleted)
        self.assertFalse(self.ds.purged)

    def test_dataset_purge(self):
        self.ds.delete(purge=True)
        # Galaxy since release_15.03 wrongly reports ds.deleted as False, see https://github.com/galaxyproject/galaxy/issues/3548
        # self.assertTrue(self.ds.deleted)
        self.assertTrue(self.ds.purged)


class TestRunWorkflow(GalaxyObjectsTestBase):

    def setUp(self):
        super(TestRunWorkflow, self).setUp()
        self.lib = self.gi.libraries.create('test_%s' % uuid.uuid4().hex)
        with open(SAMPLE_FN) as f:
            self.wf = self.gi.workflows.import_new(f.read())
        self.contents = ['one\ntwo\n', '1\n2\n']
        self.inputs = [self.lib.upload_data(_) for _ in self.contents]

    def tearDown(self):
        self.wf.delete()
        self.lib.delete()

    def _test(self, existing_hist=False, params=False):
        hist_name = 'test_%s' % uuid.uuid4().hex
        if existing_hist:
            hist = self.gi.histories.create(hist_name)
        else:
            hist = hist_name
        if params:
            params = {'Paste1': {'delimiter': 'U'}}
            sep = '_'  # 'U' maps to '_' in the paste tool
        else:
            params = None
            sep = '\t'  # default
        input_map = {'Input 1': self.inputs[0], 'Input 2': self.inputs[1]}
        sys.stderr.write(os.linesep)
        outputs, out_hist = self.wf.run(
            input_map, hist, params=params, wait=True, polling_interval=1)
        self.assertEqual(len(outputs), 1)
        out_ds = outputs[0]
        self.assertIn(out_ds.id, out_hist.dataset_ids)
        res = out_ds.get_contents()
        exp_rows = zip(*(_.splitlines() for _ in self.contents))
        exp_res = six.b("\n".join(sep.join(t) for t in exp_rows) + "\n")
        self.assertEqual(res, exp_res)
        if existing_hist:
            self.assertEqual(out_hist.id, hist.id)
        out_hist.delete(purge=True)

    def test_existing_history(self):
        self._test(existing_hist=True)

    def test_new_history(self):
        self._test(existing_hist=False)

    def test_params(self):
        self._test(params=True)


class TestRunDatasetCollectionWorkflow(GalaxyObjectsTestBase):

    def setUp(self):
        super(TestRunDatasetCollectionWorkflow, self).setUp()
        with open(SAMPLE_WF_COLL_FN) as f:
            self.wf = self.gi.workflows.import_new(f.read())
        self.hist = self.gi.histories.create('test_%s' % uuid.uuid4().hex)

    def tearDown(self):
        self.wf.delete()
        self.hist.delete(purge=True)

    def test_run_workflow_with_dataset_collection(self):
        dataset1 = self.hist.paste_content(FOO_DATA)
        dataset2 = self.hist.paste_content(FOO_DATA_2)
        collection_description = dataset_collections.CollectionDescription(
            name="MyDatasetList",
            elements=[
                dataset_collections.HistoryDatasetElement(name="sample1", id=dataset1.id),
                dataset_collections.HistoryDatasetElement(name="sample2", id=dataset2.id),
            ]
        )
        dataset_collection = self.hist.create_dataset_collection(collection_description)
        input_map = {"Input Dataset Collection": dataset_collection,
                     "Input 2": dataset1}
        outputs, out_hist = self.wf.run(input_map, self.hist, wait=True)
        self.assertEqual(len(outputs), 1)
        out_hdca = outputs[0]
        self.assertIsInstance(out_hdca, wrappers.HistoryDatasetCollectionAssociation)
        self.assertEqual(out_hdca.collection_type, 'list')
        self.assertEqual(len(out_hdca.elements), 2)
        self.assertEqual(out_hist.id, self.hist.id)


class TestJob(GalaxyObjectsTestBase):

    def setUp(self):
        super(TestJob, self).setUp()

    def test_get(self):
        job_prevs = self.gi.jobs.get_previews()
        if len(job_prevs) > 0:
            job_prev = job_prevs[0]
            self.assertIsInstance(job_prev, wrappers.JobPreview)
            job = self.gi.jobs.get(job_prev.id)
            self.assertIsInstance(job, wrappers.Job)
            self.assertEqual(job.id, job_prev.id)
        for job in self.gi.jobs.list():
            self.assertIsInstance(job, wrappers.Job)


def suite():
    loader = unittest.TestLoader()
    s = unittest.TestSuite()
    s.addTests([loader.loadTestsFromTestCase(c) for c in (
        TestWrapper,
        TestWorkflow,
        TestGalaxyInstance,
        TestLibrary,
        TestLDContents,
        TestHistory,
        TestHDAContents,
        TestRunWorkflow,
    )])
    return s


if __name__ == '__main__':
    # By default, run all tests.  To run specific tests, do the following:
    #   python -m unittest <module>.<class>.<test_method>
    tests = suite()
    RUNNER = unittest.TextTestRunner(verbosity=2)
    RUNNER.run(tests)
