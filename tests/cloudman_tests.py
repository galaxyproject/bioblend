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
        self.cm.enable_autoscaling(minimum_nodes=0,maximum_nodes=19) #20 is max on AWS
        self.cm.disable_autoscaling()
        self.cm.adjust_autoscaling(minimum_nodes=None,maximum_nodes=None)
        
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
        instance_id = "abcdef"
        self.cm.remove_node(instance_id, force=True)
        assert(False)


    def test_reboot_node(self):
        instance_id = "abcdef"
        self.cm.reboot_node(instance_id)
        assert(False)
        

    def test_autoscaling(self):
        self.cm.enable_autoscaling(minimum_nodes=0,maximum_nodes=19) #20 is max on AWS
        self.cm.disable_autoscaling()
        self.cm.adjust_autoscaling(minimum_nodes=None,maximum_nodes=None)
        assert(False)
       

    def test_get_galaxy_state(self):
        galaxy_state = self.cm.get_galaxy_state() #RUNNING, STARTING.....
        assert(False)
        
