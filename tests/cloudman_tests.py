import unittest
from mock import MagicMock
from blend import cloudman

# Some ad-hoc tests for the CloudMan API
# Expects CloudMan to be running locally
# This is fairly unreadable at the moment. This needs to be fixed.

class CloudManTest(unittest.TestCase):

    def test_basic_usage(self):
        ## Start master
        ##cluster = cloudman.StartCluster
        ##cluster.ip
        
        url = "http://127.0.0.1:42284"
        password = "password"
        
        cm = cloudman.CloudMan(url, password)
        self.assertIsNotNone(cm)

        ## Set cluster type and storage size
        cm.initialize(type="xxx", storage_size="yyy")
        
        ## Get cluster status
        # Set return value of call
        cm._make_get_request = MagicMock(return_value="{}")

        status = cm.get_status()
        self.assertIsNotNone(status)
        self.assertEquals(status, {})
        
        # Check that the correct URL was called
        cm._make_get_request.assert_called_with("/cloud/instance_state_json")
        
        ## Get nodes
        # Set return value of call
        cm._make_get_request = MagicMock(return_value="{\"instances\": []}")

        nodes = cm.get_nodes()
        self.assertIsNotNone(nodes)
        self.assertEqual(len(nodes), 0)

        # Check that the correct URL was called
        cm._make_get_request.assert_called_with("/cloud/instance_feed_json")
        
        ## Add node
        num_nodes = 10
        status = cm.add_nodes(num_nodes, type="xxx", spot_price="yyy")
        self.assertIsNotNone(status)

        # Check that the correct URL was called
        params = {'number_nodes': 10}
        cm._make_get_request.assert_called_with("/cloud/add_instances", parameters=params)
        
        ## Remove nodes
        instance_id = "abcdef"
        status = cm.remove_nodes(num_nodes, force=True)
        self.assertIsNotNone(status)


        # Check that the correct URL was called
        params = {'number_nodes': 10, 'force_termination': True}
        cm._make_get_request.assert_called_with("/cloud/remove_instances", parameters=params)
        
        cm.remove_node(instance_id, force=True)

        ## Reboot instance
        cm.reboot_node(instance_id)
        
        ## Autoscaling
        cm.enable_autoscaling(minimum_nodes=0,maximum_nodes=19) #20 is max on AWS
        cm.disable_autoscaling()
        cm.adjust_autoscaling(minimum_nodes=None,maximum_nodes=None)
        
        ## Get Galaxy DNS/Host
        galaxy_state = cm.get_galaxy_state() #RUNNING, STARTING.....
        
        ## Restart cluster
        
        ## Administration
        ## reboot master
        ## reboot service
        ## update galaxy


