"""
Tests the functionality of the BioBlend CloudMan API, without actually making
calls to a remote CloudMan instance/server. These don't actually ensure
that BioBlend is integrated with CloudMan correctly. They only ensure that
if you refactor the BioBlend CloudMan API code, that it will maintain its
current behaviour.
"""
import unittest
from unittest.mock import MagicMock

from bioblend import cloudman


class TestCloudmanMock(unittest.TestCase):

    def setUp(self):
        url = "http://127.0.0.1:42284"
        password = "password"
        self.cm = cloudman.CloudManInstance(url, password)

#    def test_initialize(self):
#        self.cm._make_get_request = MagicMock(return_value="{}")
#
#        ## Set cluster type
#        self.cm.initialize(type="Galaxy")
#
#        params = {'startup_opt': 'Galaxy'}
#        self.cm._make_get_request.assert_called_with("initialize_cluster", parameters=params)

    def test_get_status(self):
        # Set return value of call
        self.cm._make_get_request = MagicMock(return_value={})

        status = self.cm.get_status()
        self.assertNotEqual(status, None)
        self.assertEqual(status, {})

        # Check that the correct URL was called
        self.cm._make_get_request.assert_called_with("instance_state_json")

    def test_get_nodes(self):
        # Set return value of call
        self.cm._make_get_request = MagicMock(return_value={'instances': []})

        nodes = self.cm.get_nodes()
        self.assertIsNotNone(nodes)
        self.assertEqual(len(nodes), 0)

        # Check that the correct URL was called
        self.cm._make_get_request.assert_called_with("instance_feed_json")

    def test_add_nodes(self):
        self.cm._make_get_request = MagicMock(return_value="{}")
        num_nodes = 10
        status = self.cm.add_nodes(num_nodes)
        self.assertIsNotNone(status)

        # Check that the correct URL was called
        params = {'number_nodes': 10, 'instance_type': '', 'spot_price': ''}
        self.cm._make_get_request.assert_called_with("add_instances", parameters=params)

    def test_remove_nodes(self):
        self.cm._make_get_request = MagicMock(return_value="{}")
        num_nodes = 10
        status = self.cm.remove_nodes(num_nodes, force=True)
        self.assertIsNotNone(status)

        # Check that the correct URL was called
        params = {'number_nodes': 10, 'force_termination': True}
        self.cm._make_get_request.assert_called_with("remove_instances", parameters=params)

    def test_remove_node(self):
        self.cm._make_get_request = MagicMock(return_value="{}")
        instance_id = "abcdef"
        self.cm.remove_node(instance_id, force=True)

        # Check that the correct URL was called
        params = {'instance_id': "abcdef"}
        self.cm._make_get_request.assert_called_with("remove_instance", parameters=params)

    def test_reboot_node(self):
        self.cm._make_get_request = MagicMock(return_value="{}")
        instance_id = "abcdef"
        self.cm.reboot_node(instance_id)

        # Check that the correct URL was called
        params = {'instance_id': "abcdef"}
        self.cm._make_get_request.assert_called_with("reboot_instance", parameters=params)

    def test_autoscaling_enabled_true(self):
        return_json_string = {"autoscaling": {"use_autoscaling": True, "as_max": "3", "as_min": "1"}}
        self.cm._make_get_request = MagicMock(return_value=return_json_string)
        self.assertTrue(self.cm.autoscaling_enabled())

    def test_autoscaling_enabled_false(self):
        return_json_string = {"autoscaling": {"use_autoscaling": False, "as_max": "3", "as_min": "1"}}
        self.cm._make_get_request = MagicMock(return_value=return_json_string)
        self.assertFalse(self.cm.autoscaling_enabled())

    def test_enable_autoscaling(self):
        return_json_string = {"autoscaling": {"use_autoscaling": False, "as_max": "N/A", "as_min": "N/A"}}
        self.cm._make_get_request = MagicMock(return_value=return_json_string)
        self.assertFalse(self.cm.autoscaling_enabled())
        self.cm.enable_autoscaling(minimum_nodes=0, maximum_nodes=19)

        # Check that the correct URL was called
        params = {'as_min': 0, 'as_max': 19}
        self.cm._make_get_request.assert_called_with("toggle_autoscaling", parameters=params)

        return_json_string = {"autoscaling": {"use_autoscaling": True, "as_max": "19", "as_min": "0"}}
        self.cm.enable_autoscaling(minimum_nodes=0, maximum_nodes=19)

        # Check that the correct URL was called
        params = {'as_min': 0, 'as_max': 19}
        self.cm._make_get_request.assert_called_with("toggle_autoscaling", parameters=params)

    def test_disable_autoscaling(self):
        return_json_string = {"autoscaling": {"use_autoscaling": True, "as_max": "3", "as_min": "1"}}
        self.cm._make_get_request = MagicMock(return_value=return_json_string)
        self.cm.disable_autoscaling()

        self.cm._make_get_request.assert_called_with("toggle_autoscaling")

    def test_adjust_autoscaling(self):
        return_json_string = {"autoscaling": {"use_autoscaling": True, "as_max": "3", "as_min": "1"}}
        self.cm._make_get_request = MagicMock(return_value=return_json_string)
        self.cm.adjust_autoscaling(minimum_nodes=3, maximum_nodes=4)
        params = {'as_min_adj': 3, 'as_max_adj': 4}
        self.cm._make_get_request.assert_called_with("adjust_autoscaling", parameters=params)

    def test_get_galaxy_state_stopped(self):
        return_json = {"status": "'Galaxy' is not running", "srvc": "Galaxy"}
        self.cm._make_get_request = MagicMock(return_value=return_json)

        self.assertEqual(self.cm.get_galaxy_state()['status'], "'Galaxy' is not running")
        params = {'srvc': "Galaxy"}
        self.cm._make_get_request.assert_called_with("get_srvc_status", parameters=params)
