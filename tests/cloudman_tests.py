import unittest
from mock import MagicMock
from blend import cloudman

# Some ad-hoc tests for the CloudMan API
# This is fairly unreadable at the moment. This needs to be fixed.

class CloudManTest(unittest.TestCase):

    def setUp(self):
        url = "http://127.0.0.1:42284"
        password = "password"
        self.cm = cloudman.CloudMan(url, password)
        

    def test_basic_usage_against_local_instance(self):
        # Expects CloudMan to be running locally
        
        ## Start master
        #cluster = cloudman.StartCluster
        #cluster.ip
        
        self.assertIsNotNone(self.cm)

        ## Set cluster type and storage size
        self.cm.initialize(type="xxx", storage_size="yyy")
        
        ## Get cluster status
        status = self.cm.get_status()
        self.assertIsNotNone(status)
        
        ## Get nodes
        nodes = self.cm.get_nodes()
        self.assertIsNotNone(nodes)
        # There should be a master node
        self.assertEqual(len(nodes), 1)

        ## Add node
        num_nodes = 10
        status = self.cm.add_nodes(num_nodes, type="xxx", spot_price="yyy")
        self.assertIsNotNone(status)

        ## Remove nodes
        instance_id = "abcdef"
        status = self.cm.remove_nodes(num_nodes, force=True)
        self.assertIsNotNone(status)

        self.cm.remove_node(instance_id, force=True)

        ## Reboot instance
        self.cm.reboot_node(instance_id)
        
        ## Autoscaling
        # enable
        self.cm.disable_autoscaling()
        self.assertFalse(self.cm.autoscaling_enabled())
        self.cm.enable_autoscaling(minimum_nodes=0,maximum_nodes=19)
        self.assertTrue(self.cm.autoscaling_enabled())
        self.assertEquals(self.cm.get_status()['autoscaling']['as_min'], 0)
        self.assertEquals(self.cm.get_status()['autoscaling']['as_max'], 19)

        # adjust
        self.cm.adjust_autoscaling(minimum_nodes=1, maximum_nodes=2)
        self.assertEquals(self.cm.get_status()['autoscaling']['as_min'], 1)
        self.assertEquals(self.cm.get_status()['autoscaling']['as_max'], 2)

        # disable
        self.cm.disable_autoscaling()
        self.cm.adjust_autoscaling(minimum_nodes=None,maximum_nodes=None)
        self.assertFalse(self.cm.autoscaling_enabled())
        
        ## Get Galaxy DNS/Host
        galaxy_state = self.cm.get_galaxy_state() #RUNNING, STARTING.....
        
        ## Restart cluster
        
        ## Administration
        ## reboot master
        ## reboot service
        ## update galaxy


    
    def test_initialize(self):
        self.assertIsNotNone(self.cm)

        ## Set cluster type and storage size
        self.cm.initialize(type="xxx", storage_size="yyy")


    def test_get_status(self):
        # Set return value of call
        self.cm._make_get_request = MagicMock(return_value="{}")

        status = self.cm.get_status()
        self.assertIsNotNone(status)
        self.assertEquals(status, {})
        
        # Check that the correct URL was called
        self.cm._make_get_request.assert_called_with("/cloud/instance_state_json")
       

    def test_get_nodes(self):
        # Set return value of call
        self.cm._make_get_request = MagicMock(return_value="{\"instances\": []}")

        nodes = self.cm.get_nodes()
        self.assertIsNotNone(nodes)
        self.assertEqual(len(nodes), 0)

        # Check that the correct URL was called
        self.cm._make_get_request.assert_called_with("/cloud/instance_feed_json")
        

    def test_add_nodes(self):
        self.cm._make_get_request = MagicMock(return_value="{}")
        num_nodes = 10
        status = self.cm.add_nodes(num_nodes, type="xxx", spot_price="yyy")
        self.assertIsNotNone(status)

        # Check that the correct URL was called
        params = {'number_nodes': 10}
        self.cm._make_get_request.assert_called_with("/cloud/add_instances", parameters=params)
      

    def test_remove_nodes(self):
        self.cm._make_get_request = MagicMock(return_value="{}")
        num_nodes = 10
        status = self.cm.remove_nodes(num_nodes, force=True)
        self.assertIsNotNone(status)

        # Check that the correct URL was called
        params = {'number_nodes': 10, 'force_termination': True}
        self.cm._make_get_request.assert_called_with("/cloud/remove_instances", parameters=params)
        

    def test_remove_node(self):
        self.cm._make_get_request = MagicMock(return_value="{}")
        instance_id = "abcdef"
        self.cm.remove_node(instance_id, force=True)

        # Check that the correct URL was called
        params = {'instance_id': "abcdef"}
        self.cm._make_get_request.assert_called_with("/cloud/remove_instance", parameters=params)


    def test_reboot_node(self):
        self.cm._make_get_request = MagicMock(return_value="{}")
        instance_id = "abcdef"
        self.cm.reboot_node(instance_id)

        # Check that the correct URL was called
        params = {'instance_id': "abcdef"}
        self.cm._make_get_request.assert_called_with("/cloud/reboot_instance", parameters=params)

       
    def test_autoscaling_enabled_false(self):
        return_json_string = """{"autoscaling": {"use_autoscaling": false, "as_max": "N/A", "as_min": "N/A"}}"""
        self.cm._make_get_request = MagicMock(return_value=return_json_string)
        self.assertFalse(self.cm.autoscaling_enabled())


    def test_autoscaling_enabled_true(self):
        return_json_string = """{"autoscaling": {"use_autoscaling": true, "as_max": "3", "as_min": "1"}}"""
        self.cm._make_get_request = MagicMock(return_value=return_json_string)
        self.assertTrue(self.cm.autoscaling_enabled())
        

    def test_enable_autoscaling(self):
        return_json_string = """{"autoscaling": {"use_autoscaling": false, "as_max": "N/A", "as_min": "N/A"}}"""
        self.cm._make_get_request = MagicMock(return_value=return_json_string)
        self.assertFalse(self.cm.autoscaling_enabled())
        self.cm.enable_autoscaling(minimum_nodes=0,maximum_nodes=19)

        # Check that the correct URL was called
        params = {'as_min': 0, 'as_max': 19}
        self.cm._make_get_request.assert_called_with("/cloud/toggle_autoscaling", parameters=params)
        
        return_json_string = """{"autoscaling": {"use_autoscaling": true, "as_max": "19", "as_min": "0"}}"""
        self.cm.enable_autoscaling(minimum_nodes=0,maximum_nodes=19)

        # Check that the correct URL was called
        params = {'as_min': 0, 'as_max': 19}
        self.cm._make_get_request.assert_called_with("/cloud/toggle_autoscaling", parameters=params)



    def test_disable_autoscaling(self):
        return_json_string = """{"autoscaling": {"use_autoscaling": true, "as_max": "3", "as_min": "1"}}"""
        self.cm._make_get_request = MagicMock(return_value=return_json_string)
        self.cm.disable_autoscaling()

        self.cm._make_get_request.assert_called_with("/cloud/toggle_autoscaling")


    def test_adjust_autoscaling(self):
        return_json_string = """{"autoscaling": {"use_autoscaling": true, "as_max": "3", "as_min": "1"}}"""
        self.cm._make_get_request = MagicMock(return_value=return_json_string)
        self.cm.adjust_autoscaling(minimum_nodes=3,maximum_nodes=4)

        params = {'as_min': 3, 'as_max': 4} 
        self.cm._make_get_request.assert_called_with("/cloud/adjust_autoscaling", parameters=params)

       

    #def test_get_galaxy_state(self):
    #    galaxy_state = self.cm.get_galaxy_state() #RUNNING, STARTING.....
    #    assert(False)
        
