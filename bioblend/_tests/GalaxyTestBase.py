import os
import time

import bioblend
import bioblend.galaxy
from . import test_util
from .test_util import unittest

bioblend.set_stream_logger('test', level='INFO')

BIOBLEND_TEST_JOB_TIMEOUT = int(os.environ.get("BIOBLEND_TEST_JOB_TIMEOUT", "60"))


@test_util.skip_unless_galaxy()
class GalaxyTestBase(unittest.TestCase):

    def setUp(self):
        galaxy_key = os.environ['BIOBLEND_GALAXY_API_KEY']
        galaxy_url = os.environ['BIOBLEND_GALAXY_URL']
        self.gi = bioblend.galaxy.GalaxyInstance(url=galaxy_url, key=galaxy_key)

    def _test_dataset(self, history_id, contents="1\t2\t3", **kwds):
        tool_output = self.gi.tools.paste_content(contents, history_id, **kwds)
        return tool_output["outputs"][0]["id"]

    def _wait_and_verify_dataset(self, dataset_id, expected_contents, timeout_seconds=BIOBLEND_TEST_JOB_TIMEOUT):
        dataset_contents = self.gi.datasets.download_dataset(dataset_id, maxwait=timeout_seconds)
        self.assertEqual(dataset_contents, expected_contents)

    def _wait_invocation(self, invocation, wait_steps=False, timeout_seconds=10):
        galaxy_version = os.environ.get('GALAXY_VERSION', None)
        is_newer = galaxy_version == 'dev' or galaxy_version >= 'release_19.09'
        show_invocation = self.gi.invocations.show_invocation if is_newer else self.gi.workflows.show_invocation
        args = [invocation['id']] if is_newer else [invocation['workflow_id'], invocation['id']]
        for _ in range(timeout_seconds * 2):
            invocation = show_invocation(*args)
            if invocation["state"] == "scheduled":
                if wait_steps:
                    if "steps" in invocation:
                        steps_scheduled = True
                        for step in invocation["steps"]:
                            if step["state"] != "scheduled":
                                steps_scheduled = False
                                break
                        if steps_scheduled:
                            break
                else:
                    break
            time.sleep(.5)
        else:
            invocation = show_invocation(*args)
            self.assertEqual(invocation["state"], "scheduled")
