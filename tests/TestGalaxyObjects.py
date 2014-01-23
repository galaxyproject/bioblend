# pylint: disable=C0103,E1101

import sys, os, unittest, json, uuid, tempfile, urllib2, shutil
try:
    from collections import OrderedDict  # Python 2.7
except ImportError:
    OrderedDict = dict
import socket
socket.setdefaulttimeout(10.0)

import bioblend
bioblend.set_stream_logger('test', level='INFO')
import bioblend.galaxy.objects.wrappers as wrappers
import bioblend.galaxy.objects.galaxy_instance as galaxy_instance
from bioblend.galaxy.client import ConnectionError


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLE_FN = os.path.join(THIS_DIR, 'data', 'paste_columns.ga')
with open(SAMPLE_FN) as F:
    WF_DICT = json.load(F)

URL = os.environ.get('BIOBLEND_GALAXY_URL', 'http://localhost:8080')
API_KEY = os.environ['BIOBLEND_GALAXY_API_KEY']


def is_reachable(url):
    res = None
    try:
        res = urllib2.urlopen(url, timeout=1)
    except urllib2.URLError:
        return False
    if res is not None:
        res.close()
    return True


class MockWrapper(wrappers.Wrapper):

    BASE_ATTRS = frozenset(['a', 'b'])

    def __init__(self, *args, **kwargs):
        super(MockWrapper, self).__init__(*args, **kwargs)


class TestWrapper(unittest.TestCase):

    def setUp(self):
        self.d = {'a' : 1, 'b' : [2, 3],  'c': {'x': 4}}
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
        self.id = '123'
        self.wf = wrappers.Workflow(WF_DICT, id=self.id)

    def test_initialize(self):
        self.assertEqual(self.wf.id, self.id)
        self.assertEqual(self.wf.name, WF_DICT['name'])
        self.assertFalse(self.wf.is_modified)
        self.wf.annotation = 'foo'
        self.assertTrue(self.wf.is_modified)

    def test_steps(self):
        step_dicts = [v for _, v in sorted(
            WF_DICT['steps'].items(), key=lambda t: int(t[0])
            )]
        for i, s in enumerate(self.wf.steps):
            self.assertTrue(isinstance(s, wrappers.Step))
            self.assertEqual(s.name, step_dicts[i]['name'])
            if step_dicts[i]['type'] == 'data_input':
                self.assertTrue(isinstance(s, wrappers.DataInput))
            if step_dicts[i]['type'] == 'tool':
                self.assertTrue(isinstance(s, wrappers.Tool))
            self.assertTrue(s.parent is self.wf)
        self.assertFalse(self.wf.is_modified)
        self.assertEqual(len(self.wf.data_inputs()), 2)
        self.assertEqual(len(self.wf.tools()), 1)

    def test_taint(self):
        self.assertFalse(self.wf.is_modified)
        self.wf.steps[0].annotation = 'foo'
        self.assertTrue(self.wf.is_modified)

    # may pass automatically if OrderedDict is dict
    def test_inputs(self):
        inputs = OrderedDict([
            ('100', {'label': 'foo', 'value': 'bar'}),
            ('99', {'label': 'boo', 'value': 'far'}),
            ])
        wf = wrappers.Workflow(WF_DICT, inputs=inputs)
        self.assertEqual(wf.inputs, ['99', '100'])


class TestGalaxyInstance(unittest.TestCase):

    def setUp(self):
        self.gi = galaxy_instance.GalaxyInstance(URL, API_KEY)

    def test_library(self):
        name = 'test_%s' % uuid.uuid4().hex
        description, synopsis = 'D', 'S'
        lib = self.gi.libraries.create(
            name, description=description, synopsis=synopsis
            )
        self.assertEqual(lib.name, name)
        self.assertEqual(lib.description, description)
        self.assertEqual(lib.synopsis, synopsis)
        self.assertTrue(lib.id in [_.id for _ in self.gi.libraries.list()])
        self.gi.libraries.delete(lib)
        self.assertFalse(lib.is_mapped)

    def test_history(self):
        name = 'test_%s' % uuid.uuid4().hex
        hist = self.gi.histories.create(name)
        self.assertEqual(hist.name, name)
        self.assertTrue(hist.id in [_.id for _ in self.gi.histories.list()])
        self.gi.histories.delete(hist, purge=True)
        self.assertFalse(hist.is_mapped)

    def assertWorkflowEqual(self, wf1, wf2):
        self.assertEqual(len(wf1.steps), len(wf2.steps))
        for step, istep in zip(wf1.steps, wf2.steps):
            self.assertEqual(step.name, istep.name)

    def test_workflow(self):
        wf = wrappers.Workflow(WF_DICT)
        wf.name = 'test_%s' % uuid.uuid4().hex
        imported = self.gi.workflows.import_one(wf)
        self.assertWorkflowEqual(imported, wf)
        for step, istep in zip(wf.steps, imported.steps):
            self.assertEqual(step.name, istep.name)
        self.assertTrue(imported.id in [_.id for _ in self.gi.workflows.list()])
        self.gi.workflows.delete(imported)
        self.assertFalse(imported.is_mapped)

    def test_workflow_from_dict(self):
        imported = self.gi.workflows.import_one(WF_DICT)
        self.assertTrue(imported.id in [_.id for _ in self.gi.workflows.list()])
        self.gi.workflows.delete(imported)

    def test_workflow_from_json(self):
        with open(SAMPLE_FN) as f:
            imported = self.gi.workflows.import_one(f.read())
        self.assertTrue(imported.id in [_.id for _ in self.gi.workflows.list()])
        self.gi.workflows.delete(imported)

    # not very accurate:
    #   * we can't publish a wf from the API
    #   * we can't directly get another user's wf
    def test_workflow_from_shared(self):
        all_prevs = dict(
            (_.id, _) for _ in self.gi.get_workflow_previews(published=True)
            )
        pub_only_ids = set(all_prevs).difference(
            _.id for _ in self.gi.get_workflow_previews()
            )
        if pub_only_ids:
            wf_id = pub_only_ids.pop()
            imported = self.gi.import_shared_workflow(wf_id)
            self.assertTrue(isinstance(imported, wrappers.Workflow))
            self.gi.delete_workflow(imported)
        else:
            print "skipped 'manually publish a workflow to run this test'"

    def test_get_libraries(self):
        self.__test_multi_get('library')

    def test_get_histories(self):
        self.__test_multi_get('history')

    def test_get_workflows(self):
        self.__test_multi_get('workflow')

    def __test_multi_get(self, obj_type):
        if obj_type == 'library':
            create = self.gi.libraries.create
            get_objs = self.gi.libraries.list
            get_prevs = self.gi.libraries.get_previews
            delete = self.gi.libraries.delete
        elif obj_type == 'history':
            create = self.gi.histories.create
            get_objs = self.gi.histories.list
            get_prevs = self.gi.histories.get_previews
            delete = self.gi.histories.delete
        elif obj_type == 'workflow':
            def create(name):
                wf = wrappers.Workflow(WF_DICT)
                wf.name = name
                return self.gi.workflows.import_one(wf)
            get_objs = self.gi.workflows.list
            get_prevs = self.gi.workflows.get_previews
            delete = self.gi.workflows.delete
        #--
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
                delete(objs.pop())
                self.assertTrue(del_id in ids(get_prevs(deleted=True)))
            else:
                # Galaxy appends info strings to imported workflow names
                prev = get_prevs()[0]
                filtered = get_objs(name=prev.name)
                self.assertEqual(len(filtered), 1)
                self.assertEqual(filtered[0].id, prev.id)
        finally:
            for o in objs:
                delete(o)


class TestLibContents(TestGalaxyInstance):

    URL = 'http://tools.ietf.org/rfc/rfc1866.txt'

    def setUp(self):
        super(TestLibContents, self).setUp()
        self.lib = self.gi.libraries.create('test_%s' % uuid.uuid4().hex)

    def tearDown(self):
        self.gi.libraries.delete(self.lib)

    def test_folder(self):
        name, desc = 'test_%s' % uuid.uuid4().hex, 'D'
        folder = self.gi.libraries.create_folder(self.lib, name, description=desc)
        self.assertEqual(folder.name, name)
        self.assertEqual(folder.description, desc)
        self.assertEqual(folder.container_id, self.lib.id)

    def test_dataset(self):
        folder = self.gi.libraries.create_folder(self.lib, 'test_%s' % uuid.uuid4().hex)
        data = 'foo\nbar\n'
        ds = self.gi.libraries.upload_data(self.lib, data, folder=folder)
        self.assertEqual(ds.container_id, self.lib.id)
        lib = self.gi.libraries.get(self.lib.id)
        self.assertEqual(len(lib.dataset_ids), 1)
        ds_id = lib.dataset_ids[0]
        self.assertEqual(ds_id, ds.id)
        self.assertEqual(self.gi.libraries.get_dataset(lib, ds_id).id, ds.id)

    def test_dataset_from_url(self):
        if is_reachable(self.URL):
            ds = self.gi.libraries.upload_from_url(self.lib, self.URL)
            self.assertEqual(ds.container_id, self.lib.id)
            assert isinstance(ds, wrappers.Dataset)
        else:
            print "skipped 'url not reachable'"

    def test_dataset_from_local(self):
        fd, path = tempfile.mkstemp(prefix='bioblend_test_')
        os.write(fd, 'foo\nbar\n')
        os.close(fd)
        ds = self.gi.libraries.upload_from_local(self.lib, path)
        assert isinstance(ds, wrappers.Dataset)
        self.assertEqual(ds.container_id, self.lib.id)
        os.remove(path)

    def test_datasets_from_fs(self):
        tempdir = tempfile.mkdtemp(prefix='bioblend_test_')
        fnames = [os.path.join(tempdir, 'data%d.txt' % i) for i in xrange(3)]
        for fn in fnames:
            with open(fn, 'w') as f:
                f.write('foo\nbar\n')
        dss = self.gi.libraries.upload_from_galaxy_fs(
            self.lib, fnames[:2], link_data_only='link_to_files'
            )
        self.assertEqual(len(dss), 2)
        for ds, fn in zip(dss, fnames):
            self.assertEqual(ds.container_id, self.lib.id)
            self.assertEqual(ds.file_name, fn)
        dss = self.gi.libraries.upload_from_galaxy_fs(self.lib, fnames[-1])
        self.assertEqual(len(dss), 1)
        self.assertNotEqual(dss[0].file_name, fnames[-1])
        shutil.rmtree(tempdir)


class TestHistory(TestGalaxyInstance):

    def setUp(self):
        super(TestHistory, self).setUp()
        self.hist = self.gi.histories.create('test_%s' % uuid.uuid4().hex)
        self.lib = self.gi.libraries.create('test_%s' % uuid.uuid4().hex)

    def tearDown(self):
        self.gi.histories.delete(self.hist, purge=True)
        self.gi.libraries.delete(self.lib)

    def test_dataset(self):
        lds = self.gi.libraries.upload_data(self.lib, 'foo\nbar\n')
        hda = self.gi.histories.import_dataset(self.hist, lds)
        self.assertTrue(isinstance(hda, wrappers.HistoryDatasetAssociation))
        self.assertEqual(hda.container_id, self.hist.id)
        updated_hist = self.gi.histories.get(self.hist.id)
        self.assertTrue(hda.id in updated_hist.dataset_ids)

    def test_delete(self):
        hist = self.gi.histories.create('test_%s' % uuid.uuid4().hex)
        hist_id = hist.id
        hist.delete(purge=True)
        self.assertFalse(hist.is_mapped)
        try:
            h = self.gi.histories.get(hist_id)
            self.fail("Expected to get a ConnectionError but GET returned %s" % str(h))
        except ConnectionError:
            pass

    def test_import_dataset(self):
        lds = self.gi.libraries.upload_data(self.lib, 'foo\nbar\n')
        self.assertEqual(len(self.hist.dataset_ids), 0)
        hda = self.hist.import_dataset(lds)
        self.assertTrue(isinstance(hda, wrappers.HistoryDatasetAssociation))
        self.assertEqual(hda.container_id, self.hist.id)
        self.assertEqual(len(self.hist.dataset_ids), 1)
        self.assertTrue(hda.id in self.hist.dataset_ids)

    def test_get_dataset(self):
        lds = self.gi.libraries.upload_data(self.lib, 'foo\nbar\n')
        hda = self.hist.import_dataset(lds)
        retrieved = self.hist.get_dataset(hda.id)
        self.assertEqual(hda.id, retrieved.id)

    def test_get_datasets(self):
        lds = [ self.gi.libraries.upload_data(self.lib, 'foo\nbar\n'),
                self.gi.libraries.upload_data(self.lib, 'foo2\nbar2\n') ]
        hdas = [ self.hist.import_dataset(_) for _ in lds ]
        datasets = self.hist.get_datasets()
        self.assertEqual(len(lds), len(datasets))
        self.assertEqual( [ _.id for _ in hdas ], [ _.id for _ in datasets ])


class TestRunWorkflow(TestGalaxyInstance):

    def setUp(self):
        super(TestRunWorkflow, self).setUp()
        self.lib = self.gi.libraries.create('test_%s' % uuid.uuid4().hex)
        self.wf = self.gi.workflows.import_one(WF_DICT)
        self.contents = ['one\ntwo\n', '1\n2\n']
        self.inputs = [self.gi.libraries.upload_data(self.lib, c) for c in self.contents]
        self.hist_name = 'test_%s' % uuid.uuid4().hex

    def tearDown(self):
        self.gi.workflows.delete(self.wf)
        self.gi.libraries.delete(self.lib)

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
            params = {0: {'delimiter': 'U'}}
            sep = '_'  # 'U' maps to '_' in the paste tool
        else:
            params = None
            sep = '\t'  # default
        output_ids, out_hist_id = self.gi.workflows.run(
            self.wf, self.inputs, hist, params=params
            )
        sys.stdout.write(os.linesep)
        self.gi.workflows.wait(output_ids, out_hist_id, polling_interval=5)
        self.assertEqual(len(output_ids), 1)
        out_ds_id = output_ids[0]
        out_hist = self.gi.histories.get(out_hist_id)
        self.assertTrue(out_ds_id in out_hist.dataset_ids)
        out_ds = self.gi.histories.get_dataset(out_hist, out_ds_id)
        res = self.gi.datasets.get_contents(out_ds)
        self.__check_res(res, sep)
        if existing_hist:
            self.assertEqual(out_hist.id, hist.id)
        self.gi.histories.delete(out_hist, purge=True)

    def test_existing_history(self):
        self.__test(existing_hist=True)

    def test_new_history(self):
        self.__test(existing_hist=False)

    def test_params(self):
        self.__test(params=True)


def suite():
    # XXX: don't use TestLoader.loadTests* until support for Python 2.6 is dropped
    s = unittest.TestSuite()
    for t in (
        'test_initialize',
        'test_taint',
        'test_serialize',
        'test_clone',
        'test_kwargs',
        ):
        s.addTest(TestWrapper(t))
    for t in (
        'test_initialize',
        'test_steps',
        'test_taint',
        'test_inputs',
        ):
        s.addTest(TestWorkflow(t))
    #--
    for t in (
        'test_library',
        'test_history',
        'test_workflow',
        'test_workflow_from_dict',
        'test_workflow_from_json',
        'test_workflow_from_shared',
        'test_get_libraries',
        'test_get_histories',
        'test_get_workflows',
        ):
        s.addTest(TestGalaxyInstance(t))
    for t in (
        'test_folder',
        'test_dataset',
        'test_dataset_from_url',
        'test_datasets_from_fs',
        'test_dataset_from_local',
        ):
        s.addTest(TestLibContents(t))
    for t in (
        'test_dataset',
        'test_delete',
        'test_import_dataset',
        'test_get_dataset',
        'test_get_datasets',
        ):
        s.addTest(TestHistory(t))
    for t in (
        'test_existing_history',
        'test_new_history',
        'test_params',
        ):
        s.addTest(TestRunWorkflow(t))
    return s


if __name__ == '__main__':
    RUNNER = unittest.TextTestRunner(verbosity=2)
    RUNNER.run((suite()))
