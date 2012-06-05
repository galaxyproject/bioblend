import unittest
from blend import cloudman

# Some ad-hoc tests for the CloudMan API
# Expects CloudMan to be running locally
# At the moment these unit tests are fairly ineffectual. They need to be improved.

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
        status = cm.get_status()
        self.assertIsNotNone(status)
        
        ## Get nodes
        nodes = cm.get_nodes()
        self.assertIsNotNone(nodes)
        # There should only be the master node
        self.assertEqual(len(nodes), 1)
        
        ## Add node
        num_nodes = 10
        status = cm.add_nodes(num_nodes, type="xxx", spot_price="yyy")
        self.assertIsNotNone(status)
        
        ## Remove nodes
        instance_id = "abcdef"
        status = cm.remove_nodes(num_nodes, force=True)
        self.assertIsNotNone(status)

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


