import os
import tempfile
import time

from six.moves import range

import bioblend
import bioblend.galaxy
from test_util import unittest

bioblend.set_stream_logger('test', level='INFO')


class GalaxyTestBase(unittest.TestCase):

    def setUp(self):
        galaxy_key = os.environ['BIOBLEND_GALAXY_API_KEY']
        galaxy_url = os.environ['BIOBLEND_GALAXY_URL']
        self.gi = bioblend.galaxy.GalaxyInstance(url=galaxy_url, key=galaxy_key)

    def _test_dataset(self, history_id, contents="1\t2\t3", **kwds):
        tool_output = self.gi.tools.paste_content(contents, history_id, **kwds)
        return tool_output["outputs"][0]["id"]

    def _wait_and_verify_dataset(self, dataset_id, expected_contents, timeout_seconds=15):
        def _state_ready(state_str):
            if state_str == 'ok':
                return True
            elif state_str == 'error':
                raise Exception('Dataset in error state')
            return False

        # Wait for dataset
        for _ in range(timeout_seconds):
            state = self.gi.datasets.show_dataset(dataset_id)['state']
            if _state_ready(state):
                return
            bioblend.log.info("Dataset is in state %s" % state)
            time.sleep(1)
        raise Exception('Timeout expired while waiting for dataset')

        with tempfile.NamedTemporaryFile(prefix='bioblend_test_') as f:
            self.gi.datasets.download_dataset(dataset_id, file_path=f.name, use_default_filename=False)
            f.flush()
            self.assertEqual(f.read(), expected_contents)
