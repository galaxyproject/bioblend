import unittest
from mock import MagicMock
from blend import biocloudcentral

class BioCloudCentralTest(unittest.TestCase):
    def setUp(self):
        url = "http://127.0.0.1:8000"
        self.bcc = biocloudcentral.BioCloudCentral(url)

    def test_get_cloud_types(self):
        cloud_types = self.bcc.get_cloud_types()
        assertTrue(len(cloud_types) > 0)

    def test_get_amis(self):
        assertTrue(False)

    def test_get_instance_types(self):
        assertTrue(False)

    def test_create_cluster(self):
        cluster_name = "Test cluster"
        password = "password"
        cloud_type = self.bcc.get_cloud_types()[0]

        self.bcc.create_cluster(cluster_name, password, cloud_type, access_key, secret_key, instance_type, placement=zone, post_start_script=psscript, worker_script=wscript, ami=image_id)

