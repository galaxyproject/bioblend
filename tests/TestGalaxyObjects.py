import os, unittest, json, uuid, tempfile, urllib2, shutil
import bioblend.galaxy.objects.wrappers as wrappers
import bioblend.galaxy.objects.galaxy_instance as galaxy_instance

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLE_FN = os.path.join(THIS_DIR, 'data', 'SimpleWorkflow.ga')
with open(SAMPLE_FN) as f:
    WF_DESC = json.load(f)

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


class TestWrapper(unittest.TestCase):

    def setUp(self):  # pylint: disable=C0103
        self.d = {'a' : 1, 'b' : 2,  'c': 3}
        self.w = wrappers.Wrapper(self.d)

    def test_initialize(self):
        for k, v in self.d.iteritems():
            self.assertEqual(getattr(self.w, k), v)
        self.w.a = 222
        self.assertEqual(self.w.a, 222)
        self.assertEqual(self.d['a'], 1)
        self.assertRaises(KeyError, getattr, self.w, 'foo')
        self.assertRaises(KeyError, setattr, self.w, 'foo', 0)

    def test_taint(self):
        self.assertFalse(self.w.is_modified)
        self.w.a = 111
        self.assertTrue(self.w.is_modified)

    def test_serialize(self):
        self.assertEqual(wrappers.Wrapper.from_json(self.w.to_json()), self.w)


class TestWorkflow(unittest.TestCase):

    def setUp(self):  # pylint: disable=C0103
        self.id = '123'
        self.wf = wrappers.Workflow(WF_DESC, id=self.id)

    def test_initialize(self):
        self.assertEqual(self.wf.id, self.id)
        for k, v in WF_DESC.iteritems():
            if k != 'steps':
                self.assertEqual(getattr(self.wf, k), v)
        self.assertFalse(self.wf.is_modified)
        self.wf.annotation = 'foo'
        self.assertTrue(self.wf.is_modified)

    def test_steps(self):
        simple_tool_attrs = set(('tool_errors', 'tool_id', 'tool_version'))
        for s in self.wf.steps:
            self.assertTrue(s.parent is self.wf)
            s_desc = WF_DESC['steps'][str(s.id)]
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
        self.wf.steps[1].tool['iterate'] = 'no'
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
        wf = wrappers.Workflow(WF_DESC, links=links)
        self.assertEqual(wf.links['foo'], '98')
        self.assertEqual(wf.links['boo'], '99')


class TestTool(unittest.TestCase):

    def setUp(self):  # pylint: disable=C0103
        self.step = wrappers.Workflow(WF_DESC).steps[1]
        self.tool = self.step.tool

    def test_initialize(self):
        self.assertTrue(self.tool.parent is self.step)
        self.assertFalse(self.step.is_modified)

    def test_params(self):
        self.assertEqual(self.tool['exp'], '1')
        self.tool['exp'] = '2'
        self.assertEqual(self.tool['exp'], '2')
        self.assertTrue(self.step.is_modified)
        self.assertRaises(KeyError, self.tool.__getitem__, 'foo')
        self.assertRaises(KeyError, self.tool.__setitem__, 'foo', 0)


class TestGalaxyInstance(unittest.TestCase):

    def setUp(self):  # pylint: disable=C0103
        self.gi = galaxy_instance.GalaxyInstance(URL, API_KEY)

    def assertWrappedEqual(self, w1, w2, keys_to_skip=None):
        if keys_to_skip is None:
            keys_to_skip = set()
        for (k, v) in w1.iteritems():
            self.assertTrue(k in w2)
            if k not in keys_to_skip:
                self.assertEqual(w2[k], v)

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
        wf = wrappers.Workflow(WF_DESC)
        wf.name = 'test_%s' % uuid.uuid4().hex
        imported = self.gi.import_workflow(wf)
        self.assertWrappedEqual(
            wf.core.wrapped, imported.core.wrapped, set(['name', 'steps'])
            )
        self.assertEqual(len(imported.steps), len(wf.steps))
        for step, istep in zip(wf.steps, imported.steps):
            self.assertWrappedEqual(
                step.core.wrapped, istep.core.wrapped, set(['tool_state'])
                )
            if step.type == 'tool':
                self.assertWrappedEqual(step.tool.state, istep.tool.state)
        self.assertTrue(imported.id in [_.id for _ in self.gi.get_workflows()])
        self.gi.delete_workflow(imported)
        for attr in imported.id, imported.links:
            self.assertTrue(attr is None)


class TestLibContents(TestGalaxyInstance):

    URL = 'http://tools.ietf.org/rfc/rfc1866.txt'

    def setUp(self):  # pylint: disable=C0103
        super(TestLibContents, self).setUp()
        self.lib = self.gi.create_library('test_%s' % uuid.uuid4().hex)

    def tearDown(self):  # pylint: disable=C0103
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
    for t in (
        'test_library',
        'test_history',
        'test_workflow',
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
    return s


if __name__ == '__main__':
    RUNNER = unittest.TextTestRunner(verbosity=2)
    RUNNER.run((suite()))
