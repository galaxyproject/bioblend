# pylint: disable=C0103,E1101

import sys, os, json, uuid, tempfile, tarfile, urllib2, shutil
from test_util import unittest
import socket
socket.setdefaulttimeout(10.0)

import bioblend
bioblend.set_stream_logger('test', level='INFO')
import bioblend.galaxy.objects.wrappers as wrappers
import bioblend.galaxy.objects.galaxy_instance as galaxy_instance
from bioblend.galaxy.client import ConnectionError
import test_util


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLE_FN = os.path.join(THIS_DIR, 'data', 'paste_columns.ga')
FOO_DATA = 'foo\nbar\n'
FOO_DATA_2 = 'foo2\nbar2\n'
SAMPLE_WF_DICT = {
    u'deleted': False,
    u'id': u'9005c5112febe774',
    u'inputs': {
        u'571': {u'label': u'Input Dataset', u'value': u''},
        u'572': {u'label': u'Input Dataset', u'value': u''},
        },
    u'model_class': u'StoredWorkflow',
    u'name': u'paste_columns',
    u'published': False,
    u'steps': {
        u'571': {
            u'id': 571,
            u'input_steps': {},
            u'tool_id': None,
            u'tool_inputs': {u'name': u'Input Dataset'},
            u'tool_version': None,
            u'type': u'data_input',
            },
        u'572': {
            u'id': 572,
            u'input_steps': {},
            u'tool_id': None,
            u'tool_inputs': {u'name': u'Input Dataset'},
            u'tool_version': None,
            u'type': u'data_input',
            },
        u'573': {
            u'id': 573,
            u'input_steps': {
                u'input1': {u'source_step': 571, u'step_output': u'output'},
                u'input2': {u'source_step': 572, u'step_output': u'output'},
                },
            u'tool_id': u'Paste1',
            u'tool_inputs': {
                u'delimiter': u'"T"',
                u'input1': u'null',
                u'input2': u'null',
                },
            u'tool_version': u'1.0.0',
            u'type': u'tool',
            }
        },
    u'tags': [],
    u'url': u'/api/workflows/9005c5112febe774',
    }


def is_reachable(url):
    res = None
    try:
        res = urllib2.urlopen(url, timeout=1)
    except urllib2.URLError:
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
        self.d = {'a' : 1, 'b' : [2, 3], 'c': {'x': 4}}
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
        self.w.a = 111
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
        self.assertEqual(w.parent, parent)
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
            self.wf.input_labels_to_ids, {'Input Dataset': set(['571', '572'])}
            )
        self.assertEqual(
            self.wf.tool_labels_to_ids, {'Paste1': set(['573'])}
            )
        self.assertEqual(self.wf.input_ids, set(['571', '572']))
        self.assertEqual(self.wf.output_ids, set(['573']))

    def test_dag(self):
        inv_dag = {}
        for h, tails in self.wf.dag.iteritems():
            for t in tails:
                inv_dag.setdefault(str(t), set()).add(h)
        self.assertEqual(self.wf.inv_dag, inv_dag)
        heads = set(self.wf.dag)
        self.assertEqual(heads, set.union(*self.wf.inv_dag.itervalues()))
        tails = set(self.wf.inv_dag)
        self.assertEqual(tails, set.union(*self.wf.dag.itervalues()))
        ids = self.wf.sorted_step_ids()
        self.assertEqual(set(ids), heads | tails)
        for h, tails in self.wf.dag.iteritems():
            for t in tails:
                self.assertTrue(ids.index(h) < ids.index(t))

    def test_steps(self):
        steps = SAMPLE_WF_DICT['steps']
        for sid, s in self.wf.steps.iteritems():
            self.assertTrue(isinstance(s, wrappers.Step))
            self.assertEqual(s.id, sid)
            d = steps[sid]
            self.assertTrue(s.parent is self.wf)
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
            {label: [DummyLD('a'), DummyLD('b')]}
            )
        # {'571': {'id': 'a', 'src': 'ld'}, '572': {'id': 'b', 'src': 'ld'}}
        # OR
        # {'571': {'id': 'b', 'src': 'ld'}, '572': {'id': 'a', 'src': 'ld'}}
        self.assertEqual(set(input_map), set(['571', '572']))
        for d in input_map.itervalues():
            self.assertEqual(set(d), set(['id', 'src']))
            self.assertEqual(d['src'], 'ld')
            self.assertTrue(d['id'] in 'ab')


class GalaxyObjectsTestBase(unittest.TestCase):

    def setUp(self):
        galaxy_key = os.environ['BIOBLEND_GALAXY_API_KEY']
        galaxy_url = os.environ['BIOBLEND_GALAXY_URL']
        self.gi = galaxy_instance.GalaxyInstance(galaxy_url, galaxy_key)

@test_util.skip_unless_galaxy()
class TestGalaxyInstance(GalaxyObjectsTestBase):

    def test_library(self):
        name = 'test_%s' % uuid.uuid4().hex
        description, synopsis = 'D', 'S'
        lib = self.gi.libraries.create(
            name, description=description, synopsis=synopsis
            )
        self.assertEqual(lib.name, name)
        self.assertEqual(lib.description, description)
        self.assertEqual(lib.synopsis, synopsis)
        self.assertEqual(len(lib.content_infos), 1)  # root folder
        self.assertEqual(len(lib.folder_ids), 1)
        self.assertEqual(len(lib.dataset_ids), 0)
        self.assertTrue(lib.id in [_.id for _ in self.gi.libraries.list()])
        lib.delete()
        self.assertFalse(lib.is_mapped)

    def test_history(self):
        name = 'test_%s' % uuid.uuid4().hex
        hist = self.gi.histories.create(name)
        self.assertEqual(hist.name, name)
        self.assertTrue(hist.id in [_.id for _ in self.gi.histories.list()])
        hist.delete(purge=True)
        self.assertFalse(hist.is_mapped)

    def test_workflow_from_str(self):
        with open(SAMPLE_FN) as f:
            wf = self.gi.workflows.import_new(f.read())
        self.__check_and_del_workflow(wf)

    def test_workflow_from_dict(self):
        with open(SAMPLE_FN) as f:
            wf = self.gi.workflows.import_new(json.load(f))
        self.__check_and_del_workflow(wf)

    def test_workflow_missing_tools(self):
        with open(SAMPLE_FN) as f:
            wf_dump = json.load(f)
            wf_info = self.gi.gi.workflows.import_workflow_json(wf_dump)
            wf_dict = self.gi.gi.workflows.show_workflow(wf_info['id'])
            for id_, step in wf_dict['steps'].iteritems():
                if step['type'] == 'tool':
                    for k in 'tool_inputs', 'tool_version':
                        wf_dict['steps'][id_][k] = None
            wf = wrappers.Workflow(wf_dict, gi=self.gi)
            self.assertFalse(wf.is_runnable)
            self.assertRaises(RuntimeError, wf.run)
            wf.delete()

    def test_export(self):
        with open(SAMPLE_FN) as f:
            wf1 = self.gi.workflows.import_new(f.read())
        wf2 = self.gi.workflows.import_new(wf1.export())
        self.assertNotEqual(wf1.id, wf2.id)
        for wf in wf1, wf2:
            self.__check_and_del_workflow(wf)

    def __check_and_del_workflow(self, wf):
        # Galaxy appends additional text to imported workflow names
        self.assertTrue(wf.name.startswith('paste_columns'))
        self.assertEqual(len(wf.steps), 3)
        wf_ids = set(_.id for _ in self.gi.workflows.list())
        self.assertTrue(wf.id in wf_ids)
        wf.delete()

    # not very accurate:
    #   * we can't publish a wf from the API
    #   * we can't directly get another user's wf
    def test_workflow_from_shared(self):
        all_prevs = dict(
            (_.id, _) for _ in self.gi.workflows.get_previews(published=True)
            )
        pub_only_ids = set(all_prevs).difference(
            _.id for _ in self.gi.workflows.get_previews()
            )
        if pub_only_ids:
            wf_id = pub_only_ids.pop()
            imported = self.gi.workflows.import_shared(wf_id)
            self.assertTrue(isinstance(imported, wrappers.Workflow))
            imported.delete()
        else:
            print "skipped 'manually publish a workflow to run this test'"

    def test_get_libraries(self):
        self.__test_multi_get('library')

    def test_get_histories(self):
        self.__test_multi_get('history')

    def test_get_workflows(self):
        self.__test_multi_get('workflow')

    def __normalized_functions(self, obj_type):
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

    def __test_multi_get(self, obj_type):
        create, get_objs, get_prevs, del_kwargs = self.__normalized_functions(
            obj_type
            )
        ids = lambda seq: set(_.id for _ in seq)
        names = ['test_%s' % uuid.uuid4().hex for _ in xrange(2)]
        objs = []
        try:
            objs = [create(_) for _ in names]
            self.assertTrue(ids(objs) <= ids(get_objs()))
            if obj_type != 'workflow':
                filtered = get_objs(name=names[0])
                self.assertEqual(len(filtered), 1)
                self.assertEqual(filtered[0].id, objs[0].id)
                del_id = objs[-1].id
                objs.pop().delete(**del_kwargs)
                self.assertTrue(del_id in ids(get_prevs(deleted=True)))
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
        self.__test_delete_by_name('library')

    def test_delete_histories_by_name(self):
        self.__test_delete_by_name('history')

    def test_delete_workflows_by_name(self):
        self.__test_delete_by_name('workflow')

    def __test_delete_by_name(self, obj_type):
        create, _, get_prevs, del_kwargs = self.__normalized_functions(
            obj_type
            )
        name = 'test_%s' % uuid.uuid4().hex
        objs = [create(name) for _ in xrange(2)]
        final_name = objs[0].name
        prevs = [_ for _ in get_prevs(name=final_name) if not _.deleted]
        self.assertEqual(len(prevs), len(objs))
        del_kwargs['name'] = final_name
        objs[0].gi_module.delete(**del_kwargs)
        prevs = [_ for _ in get_prevs(name=final_name) if not _.deleted]
        self.assertEqual(len(prevs), 0)


@test_util.skip_unless_galaxy()
class TestLibrary(GalaxyObjectsTestBase):

    # just something that can be expected to be always up
    DS_URL = 'http://tools.ietf.org/rfc/rfc1866.txt'

    def setUp(self):
        super(TestLibrary, self).setUp()
        self.lib = self.gi.libraries.create('test_%s' % uuid.uuid4().hex)

    def tearDown(self):
        self.lib.delete()

    def test_folder(self):
        name, desc = 'test_%s' % uuid.uuid4().hex, 'D'
        folder = self.lib.create_folder(name, description=desc)
        self.assertEqual(folder.name, name)
        self.assertEqual(folder.description, desc)
        self.assertEqual(folder.container_id, self.lib.id)
        self.assertEqual(len(self.lib.content_infos), 2)
        self.assertEqual(len(self.lib.folder_ids), 2)
        self.assertEqual(len(self.lib.dataset_ids), 0)
        self.assertTrue(folder.id in self.lib.folder_ids)

    def __check_datasets(self, dss):
        self.assertEqual(len(dss), len(self.lib.dataset_ids))
        self.assertEqual(set(_.id for _ in dss), set(self.lib.dataset_ids))
        for ds in dss:
            self.assertTrue(ds.container is self.lib)

    def test_dataset(self):
        folder = self.lib.create_folder('test_%s' % uuid.uuid4().hex)
        ds = self.lib.upload_data(FOO_DATA, folder=folder)
        self.assertEqual(len(self.lib.content_infos), 3)
        self.assertEqual(len(self.lib.folder_ids), 2)
        self.__check_datasets([ds])

    def test_dataset_from_url(self):
        if is_reachable(self.DS_URL):
            ds = self.lib.upload_from_url(self.DS_URL)
            self.__check_datasets([ds])
        else:
            print "skipped 'url not reachable'"

    def test_dataset_from_local(self):
        with tempfile.NamedTemporaryFile(prefix='bioblend_test_') as f:
            f.write(FOO_DATA)
            f.flush()
            ds = self.lib.upload_from_local(f.name)
        self.__check_datasets([ds])

    def test_datasets_from_fs(self):
        bnames = ['f%d.txt' % i for i in xrange(2)]
        dss, fnames = upload_from_fs(self.lib, bnames)
        self.__check_datasets(dss)
        dss, fnames = upload_from_fs(
            self.lib, bnames, link_data_only='link_to_files'
            )
        for ds, fn in zip(dss, fnames):
            self.assertEqual(ds.file_name, fn)

    def test_get_dataset(self):
        ds = self.lib.upload_data(FOO_DATA)
        retrieved = self.lib.get_dataset(ds.id)
        self.assertEqual(ds.id, retrieved.id)

    def test_get_datasets(self):
        bnames = ['f%d.txt' % _ for _ in xrange(2)]
        dss, _ = upload_from_fs(self.lib, bnames)
        retrieved = self.lib.get_datasets()
        self.assertEqual(len(dss), len(retrieved))
        self.assertEqual(set(_.id for _ in dss), set(_.id for _ in retrieved))
        name = '/%s' % bnames[0]
        selected = self.lib.get_datasets(name=name)
        self.assertEqual(len(selected), 1)
        self.assertEqual(selected[0].name, bnames[0])


@test_util.skip_unless_galaxy()
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
            self.assertEqual(str(FOO_DATA[idx]), c)

    def test_dataset_peek(self):
        fetched_data = self.ds.peek(chunk_size=4)
        self.assertEqual(FOO_DATA[0:4], fetched_data)

    def test_dataset_download(self):
        with tempfile.TemporaryFile() as f:
            self.ds.download(f)
            f.seek(0)
            self.assertEqual(FOO_DATA, f.read())

    def test_dataset_get_contents(self):
        self.assertEqual(FOO_DATA, self.ds.get_contents())


@test_util.skip_unless_galaxy()
class TestHistory(GalaxyObjectsTestBase):

    def setUp(self):
        super(TestHistory, self).setUp()
        self.hist = self.gi.histories.create('test_%s' % uuid.uuid4().hex)
        self.lib = self.gi.libraries.create('test_%s' % uuid.uuid4().hex)

    def tearDown(self):
        self.hist.delete(purge=True)
        self.lib.delete()

    def test_delete(self):
        hist = self.gi.histories.create('test_%s' % uuid.uuid4().hex)
        hist_id = hist.id
        hist.delete(purge=True)
        self.assertFalse(hist.is_mapped)
        try:
            h = self.gi.histories.get(hist_id)
            self.fail("Expected ConnectionError but GET returned %s" % str(h))
        except ConnectionError:
            pass

    def test_import_dataset(self):
        lds = self.lib.upload_data(FOO_DATA)
        self.assertEqual(len(self.hist.dataset_ids), 0)
        hda = self.hist.import_dataset(lds)
        self.assertTrue(isinstance(hda, wrappers.HistoryDatasetAssociation))
        self.assertTrue(hda.container is self.hist)
        self.assertEqual(len(self.hist.dataset_ids), 1)
        self.assertEqual(self.hist.dataset_ids[0], hda.id)

    def test_get_dataset(self):
        lds = self.lib.upload_data(FOO_DATA)
        hda = self.hist.import_dataset(lds)
        retrieved = self.hist.get_dataset(hda.id)
        self.assertEqual(hda.id, retrieved.id)

    def test_get_datasets(self):
        bnames = ['f%d.txt' % _ for _ in xrange(2)]
        lds, _ = upload_from_fs(self.lib, bnames)
        hdas = [self.hist.import_dataset(_) for _ in lds]
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
            with open(temp_fn, 'w') as fo:
                self.hist.download(jeha_id, fo)
            self.assertTrue(tarfile.is_tarfile(temp_fn))
        finally:
            shutil.rmtree(tempdir)

    def test_update(self):
        new_name = 'test_%s' % uuid.uuid4().hex
        new_annotation = 'Annotation for %s' % new_name
        updated_hist = self.hist.update(name=new_name, annotation=new_annotation)
        self.assertEqual(self.hist.id, updated_hist.id)
        self.assertEqual(self.hist.name, new_name)
        self.assertEqual(self.hist.annotation, new_annotation)


@test_util.skip_unless_galaxy()
class TestHDAContents(GalaxyObjectsTestBase):

    def setUp(self):
        super(TestHDAContents, self).setUp()
        self.hist = self.gi.histories.create('test_%s' % uuid.uuid4().hex)
        self.lib = self.gi.libraries.create('test_%s' % uuid.uuid4().hex)
        ld = self.lib.upload_data(FOO_DATA)
        self.ds = self.hist.import_dataset(ld)
        self.ds.wait()

    def tearDown(self):
        self.hist.delete(purge=True)
        self.lib.delete()

    def test_dataset_get_stream(self):
        for idx, c in enumerate(self.ds.get_stream(chunk_size=1)):
            self.assertEqual(str(FOO_DATA[idx]), c)

    def test_dataset_peek(self):
        fetched_data = self.ds.peek(chunk_size=4)
        self.assertEqual(FOO_DATA[0:4], fetched_data)

    def test_dataset_download(self):
        with tempfile.TemporaryFile() as f:
            self.ds.download(f)
            f.seek(0)
            data = f.read()
            self.assertEqual(FOO_DATA, data)

    def test_dataset_get_contents(self):
        self.assertEqual(FOO_DATA, self.ds.get_contents())


@test_util.skip_unless_galaxy()
class TestRunWorkflow(GalaxyObjectsTestBase):

    def setUp(self):
        super(TestRunWorkflow, self).setUp()
        self.lib = self.gi.libraries.create('test_%s' % uuid.uuid4().hex)
        with open(SAMPLE_FN) as f:
            self.wf = self.gi.workflows.import_new(f.read())
        self.contents = ['one\ntwo\n', '1\n2\n']
        self.inputs = [self.lib.upload_data(_) for _ in self.contents]
        self.hist_name = 'test_%s' % uuid.uuid4().hex

    def tearDown(self):
        self.wf.delete()
        self.lib.delete()

    def __check_res(self, res, sep):
        exp_rows = zip(*(_.splitlines() for _ in self.contents))
        exp_res = "\n".join(sep.join(t) for t in exp_rows)
        self.assertEqual(res.strip(), exp_res)

    def __test(self, existing_hist=False, params=False):
        if existing_hist:
            hist = self.gi.histories.create(self.hist_name)
        else:
            hist = self.hist_name
        if params:
            params = {'Paste1': {'delimiter': 'U'}}
            sep = '_'  # 'U' maps to '_' in the paste tool
        else:
            params = None
            sep = '\t'  # default
        input_map = {'Input 1': self.inputs[0], 'Input 2': self.inputs[1]}
        sys.stderr.write(os.linesep)
        outputs, out_hist = self.wf.run(
            input_map, hist, params=params, wait=True, polling_interval=1
            )
        self.assertEqual(len(outputs), 1)
        out_ds = outputs[0]
        self.assertTrue(out_ds.id in out_hist.dataset_ids)
        res = out_ds.get_contents()
        self.__check_res(res, sep)
        if existing_hist:
            self.assertEqual(out_hist.id, hist.id)
        out_hist.delete(purge=True)

    def test_existing_history(self):
        self.__test(existing_hist=True)

    def test_new_history(self):
        self.__test(existing_hist=False)

    def test_params(self):
        self.__test(params=True)


# XXX: don't use TestLoader.loadTests* until support for Python 2.6 is dropped
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
