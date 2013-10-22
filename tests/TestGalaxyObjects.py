import os, unittest, json
import bioblend.galaxy.objects.wrappers as wrappers

THIS_DIR = os.path.dirname(os.path.abspath(__file__))
SAMPLE_FN = os.path.join(THIS_DIR, "data", "SampleWorkflow.ga")
with open(SAMPLE_FN) as f:
    WF_DESC = json.load(f)


class TestWrapper(unittest.TestCase):

    def setUp(self):
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

    def setUp(self):
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
        self.wf.steps[2].tool['global_model'] = 'foo'
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

    def setUp(self):
        self.step = wrappers.Workflow(WF_DESC).steps[2]
        self.tool = self.step.tool

    def test_initialize(self):
        self.assertTrue(self.tool.parent is self.step)
        self.assertFalse(self.step.is_modified)

    def test_params(self):
        self.assertEqual(self.tool['do_normalization'], "No")
        self.tool['do_normalization'] = "Yes"
        self.assertEqual(self.tool['do_normalization'], "Yes")
        self.assertTrue(self.step.is_modified)
        self.assertRaises(KeyError, self.tool.__getitem__, 'foo')
        self.assertRaises(KeyError, self.tool.__setitem__, 'foo', 0)


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
    return s


if __name__ == '__main__':
    RUNNER = unittest.TextTestRunner(verbosity=2)
    RUNNER.run((suite()))
