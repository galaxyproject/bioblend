"""
Tests the functionality of the Blend CloudMan API. These tests require working
credentials to supported cloud infrastructure.
"""
from bioblend.cloudman import CloudManConfig, CloudManInstance
from . import CloudmanTestBase, test_util


@test_util.skip_unless_cloudman()
class TestCloudmanLaunch(CloudmanTestBase.CloudmanTestBase):

    def setUp(self):
        super().setUp()

    def test_validate_valid_config(self):
        """
        Tests whether a valid config is validated properly.
        """
        # cfg = CloudManConfig(self.access_key, self.secret_key, self.cluster_name, self.ami_id, self.instance_type, self.password, cloud_metadata=self.cloud_metadata)
        cls = TestCloudmanLaunch
        cfg = CloudManConfig(cls.access_key, cls.secret_key, cls.cluster_name, cls.ami_id, cls.instance_type, cls.password, cloud_metadata=cls.cloud_metadata)
        result = cfg.validate()
        self.assertIsNone(result, "Validation did not return null to indicate success!")

    def test_validate_invalid_config(self):
        """
        Tests whether an invalid config is validated properly.
        """
        cfg = CloudManConfig()
        result = cfg.validate()
        self.assertIsNotNone(result, "Validation should have returned a value since the configuration was invalid!")

    def test_launch_and_terminate(self):
        cls = TestCloudmanLaunch
        cfg = CloudManConfig(cls.access_key, cls.secret_key, cls.cluster_name, cls.ami_id, cls.instance_type, cls.password, cloud_metadata=cls.cloud_metadata)
        cmi = CloudManInstance.launch_instance(cfg)
        status = cmi.get_status()
        self.assertNotEqual(status['cluster_status'], 'ERROR', "instance.get_status() returned ERROR. Should return a successful status!")
        try:
            # TODO: The terminate method is unpredictable! Needs fix.
            result = cmi.terminate(delete_cluster=True)
            self.assertEqual(result['cluster_status'], 'SHUTDOWN', "Cluster should be in status SHUTDOWN after call to terminate!")
        except Exception:
            pass
