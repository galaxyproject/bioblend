# pylint: disable=C0103

import sys, os, unittest, json, uuid, tempfile, urllib2, shutil

import bioblend
bioblend.set_stream_logger('test', level='INFO')
import bioblend.galaxy.objects.wrappers as wrappers
import bioblend.galaxy.objects.galaxy_instance as galaxy_instance


THIS_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLE_FN = os.path.join(THIS_DIR, 'data', 'paste_columns.ga')
with open(SAMPLE_FN) as F:
    WF_DICT = json.load(F)

URL = os.environ.get('BIOBLEND_GALAXY_URL', 'http://localhost:8080')
API_KEY = os.environ['BIOBLEND_GALAXY_API_KEY']


def first_tool_idx(wf_dict):
    return int((
        k for k, v in wf_dict['steps'].iteritems() if v['type'] == 'tool'
        ).next())


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

    def __init__(self, wrapped, parent=None):
        super(MockWrapper, self).__init__(wrapped, parent=parent)


class TestWrapper(unittest.TestCase):

    def setUp(self):
        self.d = {'a' : 1, 'b' : [2, 3],  'c': {'x': 4}}
        self.assertRaises(TypeError, wrappers.Wrapper, self.d)
        self.w = MockWrapper(self.d)

    def test_initialize(self):
        for k, v in self.d.iteritems():
            self.assertEqual(getattr(self.w, k), v)
        self.w.a = 222
        self.w.b[0] = 222
        self.assertEqual(self.w.a, 222)
        self.assertEqual(self.w.b[0], 222)
        self.assertEqual(self.d['a'], 1)
        self.assertEqual(self.d['b'][0], 2)
        self.assertRaises(KeyError, getattr, self.w, 'foo')
        self.assertRaises(KeyError, setattr, self.w, 'foo', 0)

    def test_taint(self):
        self.assertFalse(self.w.is_modified)
        self.w.a = 111
        self.assertTrue(self.w.is_modified)

    def test_serialize(self):
        w2 = MockWrapper.from_json(self.w.to_json())
        self.assertEqual(w2.core.wrapped, self.w.core.wrapped)


class TestWorkflow(unittest.TestCase):

    def setUp(self):
        self.id = '123'
        self.wf = wrappers.Workflow(WF_DICT, id=self.id)

    def test_initialize(self):
        self.assertEqual(self.wf.id, self.id)
        for k, v in WF_DICT.iteritems():
            if k != 'steps':
                self.assertEqual(getattr(self.wf, k), v)
        self.assertFalse(self.wf.is_modified)
        self.wf.annotation = 'foo'
        self.assertTrue(self.wf.is_modified)

    def test_steps(self):
        simple_tool_attrs = set(('tool_errors', 'tool_id', 'tool_version'))
        for s in self.wf.steps:
            self.assertTrue(s.parent is self.wf)
            s_desc = WF_DICT['steps'][str(s.id)]
            for k, v in s_desc.iteritems():
                if s.type == 'tool' and k in simple_tool_attrs:
                    self.assertEqual(getattr(s.tool, k.replace('tool_', '')), v)
                else:
                    self.assertEqual(getattr(s, k), v)
        self.assertFalse(self.wf.is_modified)

    def test_step_taint(self):
        self.assertFalse(self.wf.is_modified)
        self.wf.steps[0].annotation = 'foo'
        self.assertTrue(self.wf.is_modified)

    def test_tool_taint(self):
        self.assertFalse(self.wf.is_modified)
        self.wf.steps[first_tool_idx(WF_DICT)].tool['chromInfo'] = 'foo'
        self.assertTrue(self.wf.is_modified)

    def test_clone(self):
        wf = self.wf.clone()
        self.assertTrue(wf.id is None)
        self.assertNotEqual(wf, self.wf)
        self.assertEqual(
            json.loads(wf.to_json()), json.loads(self.wf.to_json())
            )

    def test_links(self):
        links = {
            '98': {'label': 'foo', 'value': 'bar'},
            '99': {'label': 'boo', 'value': 'far'},
            }
        wf = wrappers.Workflow(WF_DICT, links=links)
        self.assertEqual(len(wf.links), len(links))
        for input_link in wf.links:
            link_dict = links.get(input_link.id)
            self.assertTrue(link_dict is not None)
            for k, v in link_dict.iteritems():
                a = getattr(input_link, k, None)
                self.assertEqual(a, v)


class TestTool(unittest.TestCase):

    def setUp(self):
        self.step = wrappers.Workflow(WF_DICT).steps[first_tool_idx(WF_DICT)]
        self.tool = self.step.tool

    def test_initialize(self):
        self.assertTrue(self.tool.parent is self.step)
        self.assertFalse(self.step.is_modified)

    def test_params(self):
        self.assertNotEqual(self.tool['chromInfo'], 'foo')
        self.tool['chromInfo'] = 'foo'
        self.assertEqual(self.tool['chromInfo'], 'foo')
        self.assertTrue(self.step.is_modified)
        self.assertRaises(KeyError, self.tool.__getitem__, 'foo')
        self.assertRaises(KeyError, self.tool.__setitem__, 'foo', 0)


class TestGalaxyInstance(unittest.TestCase):

    def setUp(self):
        self.gi = galaxy_instance.GalaxyInstance(URL, API_KEY)

    def assertWrappedEqual(self, w1, w2, keys_to_skip=None):
        if keys_to_skip is None:
            keys_to_skip = set()
        for (k, v) in w1.iteritems():
            self.assertTrue(k in w2)
            if k not in keys_to_skip:
                self.assertEqual(w2[k], v, "%r: %r != %r" % (k, w2[k], v))

    def test_library(self):
        name = 'test_%s' % uuid.uuid4().hex
        description, synopsis = 'D', 'S'
        lib = self.gi.create_library(
            name, description=description, synopsis=synopsis
            )
        self.assertEqual(lib.name, name)
        self.assertEqual(lib.description, description)
        self.assertEqual(lib.synopsis, synopsis)
        self.assertTrue(lib.id in [_.id for _ in self.gi.get_libraries()])
        self.gi.delete_library(lib)
        self.assertTrue(lib.id is None)

    def test_history(self):
        name = 'test_%s' % uuid.uuid4().hex
        hist = self.gi.create_history(name)
        self.assertEqual(hist.name, name)
        self.assertTrue(hist.id in [_.id for _ in self.gi.get_histories()])
        self.gi.delete_history(hist)
        self.assertTrue(hist.id is None)

    def test_workflow(self):
        wf = wrappers.Workflow(WF_DICT)
        wf.name = 'test_%s' % uuid.uuid4().hex
        imported = self.gi.import_workflow(wf)
        self.assertWrappedEqual(
            wf.core.wrapped, imported.core.wrapped, set(['name', 'steps'])
            )
        self.assertEqual(len(imported.steps), len(wf.steps))
        keys_to_skip = set(['tool_state', 'tool_version'])
        for step, istep in zip(wf.steps, imported.steps):
            self.assertWrappedEqual(
                step.core.wrapped, istep.core.wrapped, keys_to_skip
                )
            if step.type == 'tool':
                self.assertWrappedEqual(step.tool.state, istep.tool.state)
        self.assertTrue(imported.id in [_.id for _ in self.gi.get_workflows()])
        self.gi.delete_workflow(imported)
        for attr in imported.id, imported.links:
            self.assertTrue(attr is None)

    def test_workflow_from_dict(self):
        imported = self.gi.import_workflow(WF_DICT)
        self.assertTrue(imported.id in [_.id for _ in self.gi.get_workflows()])
        self.gi.delete_workflow(imported)

    def test_workflow_from_json(self):
        with open(SAMPLE_FN) as f:
            imported = self.gi.import_workflow(f.read())
        self.assertTrue(imported.id in [_.id for _ in self.gi.get_workflows()])
        self.gi.delete_workflow(imported)


class TestLibContents(TestGalaxyInstance):

    URL = 'http://tools.ietf.org/rfc/rfc1866.txt'

    def setUp(self):
        super(TestLibContents, self).setUp()
        self.lib = self.gi.create_library('test_%s' % uuid.uuid4().hex)

    def tearDown(self):
        self.gi.delete_library(self.lib)

    def test_folder(self):
        name, desc = 'test_%s' % uuid.uuid4().hex, 'D'
        folder = self.gi.create_folder(self.lib, name, description=desc)
        self.assertEqual(folder.name, name)
        self.assertEqual(folder.description, desc)
        self.assertTrue(folder.library is self.lib)

    def test_dataset(self):
        folder = self.gi.create_folder(self.lib, 'test_%s' % uuid.uuid4().hex)
        data = 'foo\nbar\n'
        ds = self.gi.upload_data(self.lib, data, folder=folder)
        self.assertEqual(ds.folder_id, folder.id)
        lib = self.gi.get_library(self.lib.id)
        self.assertEqual(len(lib.datasets), 1)
        self.assertEqual(lib.datasets[0].id, ds.id)

    def test_dataset_from_url(self):
        if is_reachable(self.URL):
            ds = self.gi.upload_from_url(self.lib, self.URL)
            assert isinstance(ds, wrappers.Dataset)
        else:
            print "skipped 'url not reachable'"

    def test_dataset_from_local(self):
        fd, path = tempfile.mkstemp(prefix='bioblend_test_')
        os.write(fd, 'foo\nbar\n')
        os.close(fd)
        ds = self.gi.upload_from_local(self.lib, path)
        assert isinstance(ds, wrappers.Dataset)
        os.remove(path)

    def test_datasets_from_fs(self):
        tempdir = tempfile.mkdtemp(prefix='bioblend_test_')
        fnames = [os.path.join(tempdir, 'data%d.txt' % i) for i in xrange(3)]
        for fn in fnames:
            with open(fn, 'w') as f:
                f.write('foo\nbar\n')
        dss = self.gi.upload_from_galaxy_fs(
            self.lib, fnames[:2], link_data_only='link_to_files'
            )
        self.assertEqual(len(dss), 2)
        for ds, fn in zip(dss, fnames):
            self.assertEqual(ds.file_name, fn)
        dss = self.gi.upload_from_galaxy_fs(self.lib, fnames[-1])
        self.assertEqual(len(dss), 1)
        self.assertNotEqual(dss[0].file_name, fnames[-1])
        shutil.rmtree(tempdir)


class TestHistContents(TestGalaxyInstance):

    def setUp(self):
        super(TestHistContents, self).setUp()
        self.hist = self.gi.create_history('test_%s' % uuid.uuid4().hex)

    def tearDown(self):
        self.gi.delete_history(self.hist)

    def test_dataset(self):
        lib = self.gi.create_library('test_%s' % uuid.uuid4().hex)
        lds = self.gi.upload_data(lib, 'foo\nbar\n')
        hda = self.gi.import_dataset_to_history(self.hist, lds)
        self.assertTrue(isinstance(hda, wrappers.HistoryDatasetAssociation))
        updated_hist = self.gi.get_history(self.hist.id)
        self.assertTrue(hda.id in set(_.id for _ in updated_hist.datasets))
        self.gi.delete_library(lib)


class TestRunWorkflow(TestGalaxyInstance):

    def setUp(self):
        super(TestRunWorkflow, self).setUp()
        self.lib = self.gi.create_library('test_%s' % uuid.uuid4().hex)
        self.wf = self.gi.import_workflow(WF_DICT)
        self.contents = ['one\ntwo\n', '1\n2\n']
        self.inputs = [self.gi.upload_data(self.lib, c) for c in self.contents]
        self.hist_name = 'test_%s' % uuid.uuid4().hex

    def tearDown(self):
        self.gi.delete_workflow(self.wf)
        self.gi.delete_library(self.lib)

    def __check_res(self, res, sep):
        exp_rows = zip(*(_.splitlines() for _ in self.contents))
        exp_res = "\n".join(sep.join(t) for t in exp_rows)
        # sometimes inputs are swapped - this is not deterministic
        alt_exp_res = "\n".join(sep.join(t[::-1]) for t in exp_rows)
        res = res.strip()
        self.assertTrue(res == exp_res or res == alt_exp_res)

    def __test(self, existing_hist=False, params=False):
        if existing_hist:
            hist = self.gi.create_history(self.hist_name)
        else:
            hist = self.hist_name
        if params:
            params = [{'delimiter': 'U'}]
            sep = '_'  # 'U' maps to '_' in the paste tool
        else:
            params = None
            sep = '\t'  # default
        outputs, out_hist = self.gi.run_workflow(
            self.wf, self.inputs, hist, params=params
            )
        sys.stdout.write(os.linesep)
        self.gi.wait(outputs, out_hist, polling_interval=5)
        self.assertEqual(len(outputs), 1)
        out_ds = outputs[0]
        self.assertTrue(out_ds.id in set(_.id for _ in out_hist.datasets))
        res = self.gi.get_contents(out_ds, out_hist)
        self.__check_res(res, sep)
        if existing_hist:
            self.assertEqual(out_hist.id, hist.id)
            self.gi.delete_history(hist)

    def test_existing_history(self):
        self.__test(existing_hist=True)

    def test_new_history(self):
        self.__test(existing_hist=False)

    def test_params(self):
        self.__test(params=True)


def suite():
    s = unittest.TestSuite()
    for t in (
        'test_initialize',
        'test_taint',
        'test_serialize',
        ):
        s.addTest(TestWrapper(t))
    for t in (
        'test_initialize',
        'test_steps',
        'test_step_taint',
        'test_tool_taint',
        'test_clone',
        'test_links',
        ):
        s.addTest(TestWorkflow(t))
    for t in (
        'test_initialize',
        'test_params',
        ):
        s.addTest(TestTool(t))
    #--
    for t in (
        'test_library',
        'test_history',
        'test_workflow',
        'test_workflow_from_dict',
        'test_workflow_from_json',
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
        ):
        s.addTest(TestHistContents(t))
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
