"""
Tests the functionality of the Blend CloudMan API. These tests require working
credentials to supported cloud infrastructure. 

Use ``nose`` to run these unit tests.
"""
from bioblend.cloudman import CloudManConfig
from bioblend.cloudman import CloudManInstance
import CloudmanTestBase

class TestCloudmanServices(CloudmanTestBase.CloudmanTestBase):

    @classmethod
    def setUpClass(cls):
        super(TestCloudmanServices, cls).setUpClass()
        cls.cfg = CloudManConfig(cls.access_key, cls.secret_key, cls.cluster_name, cls.ami_id, cls.instance_type, cls.password, cloud_metadata=cls.cloud_metadata)
        cls.cmi = CloudManInstance.launch_instance(cls.cfg)
        
    def setUp(self):
        self.cmi = self.__class__.cmi
        
    def test_get_status(self):
        status = self.cmi.get_status()
        self.assertNotEqual(status, None)

    def test_get_nodes(self):
        nodes = self.cmi.get_nodes()
        self.assertNotEqual(nodes, None)

    def test_add_nodes(self):
        num_nodes = 1
        status = self.cmi.add_nodes(num_nodes)
        self.assertNotEqual(status, None)

    def test_reboot_node(self):        
        instance_id = self.cmi.instance_id
        self.cmi.reboot_node(instance_id)

    def test_remove_node(self):
        instance_id = self.cmi.instance_id
        self.cmi.remove_node(instance_id, force=True)

    def test_enable_autoscaling(self):
        self.assertFalse(self.cmi.autoscaling_enabled())
        self.cmi.enable_autoscaling(minimum_nodes=0,maximum_nodes=19)
        self.assertTrue(self.cmi.autoscaling_enabled())

    def test_disable_autoscaling(self):
        self.cmi.disable_autoscaling()
        self.assertFalse(self.cmi.autoscaling_enabled())

    def test_adjust_autoscaling(self):
        self.cmi.adjust_autoscaling(minimum_nodes=3,maximum_nodes=4)

#    def test_get_galaxy_state_stopped(self):
#        self.assertEquals(self.cmi.get_galaxy_state(), "'Galaxy' is not running")
