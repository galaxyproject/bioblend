import unittest
from mock import MagicMock
from blend import cloudman

class CloudManTest(unittest.TestCase):

    def test_basic_usage_against_local_instance(self):
        url = "http://127.0.0.1:42284"
        password = "password"
        self.cm = cloudman.CloudMan(url, password)
        
        # Expects CloudMan to be running locally
        ## Set cluster type and storage size
        self.cm.initialize(type="xxx", storage_size="yyy")
        
        ## Get cluster status
        status = self.cm.get_status()
        self.assertIsNotNone(status)
        
        ## Get nodes
        nodes = self.cm.get_nodes()
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
        self.cm.adjust_autoscaling(minimum_nodes=5, maximum_nodes=10)
        self.assertEquals(self.cm.get_status()['autoscaling']['as_min'], 5)
        self.assertEquals(self.cm.get_status()['autoscaling']['as_max'], 10)

        # disable
        self.cm.disable_autoscaling()
        self.cm.adjust_autoscaling(minimum_nodes=None,maximum_nodes=None)
        self.assertFalse(self.cm.autoscaling_enabled())
        
        ## Get Galaxy DNS/Host
        galaxy_state = self.cm.get_galaxy_state() #RUNNING, STARTING.....
        
