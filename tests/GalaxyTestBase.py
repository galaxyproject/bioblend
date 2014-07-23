import os
from bioblend import galaxy
from test_util import unittest


class GalaxyTestBase(unittest.TestCase):

    def setUp(self):
        galaxy_key = os.environ['BIOBLEND_GALAXY_API_KEY']
        galaxy_url = os.environ['BIOBLEND_GALAXY_URL']
        self.gi = galaxy.GalaxyInstance(url=galaxy_url, key=galaxy_key)

    def _test_dataset(self, history_id, contents="1\t2\t3", **kwds):
        tool_output = self.gi.tools.paste_content(contents, history_id, **kwds)
        return tool_output["outputs"][0]["id"]
