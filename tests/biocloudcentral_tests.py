import unittest
from mock import MagicMock
from blend import biocloudcentral
import simplejson

class BioCloudCentralTest(unittest.TestCase):
    def setUp(self):
        url = "http://127.0.0.1:8000"
        self.bcc = biocloudcentral.BioCloudCentral(url)

    def test_get_cloud_types(self):
        cloud_hash = {
                'id': '0',
                'name': 'Test Cloud',
                'cloud_type': 'Test Type',
                'region_name': 'Test Region',
                'bucket_default': 'test_bucket',
                'region_endpoint': 'test_endpoint',
                'ec2_port': '123',
                'ec2_conn_path': '/test/connection',
                'cidr_range': '0-1',
                'is_secure': 'False',
                's3_host': 'test_host',
                's3_port': 'test_port',
                's3_conn_path': '/test_path',
        }
        self.bcc._make_get_request = MagicMock(return_value=simplejson.dumps([cloud_hash]))

        cloud_types = self.bcc.get_cloud_types()
        self.bcc._make_get_request.assert_called_with("/api/get_cloud_types")
        self.assertTrue(len(cloud_types) == 1)


    def test_get_images(self):
        images_hash = {
                'id': '0'
                }
        self.bcc._make_get_request = MagicMock(return_value=simplejson.dumps([images_hash]))

        images = self.bcc.get_images()
        self.bcc._make_get_request.assert_called_with("/api/get_images")
        self.assertTrue(len(images) == 1)


    def test_get_instance_types(self):
        instance_hash = {
                'id': '0'
                }
        self.bcc._make_get_request = MagicMock(return_value=simplejson.dumps([instance_hash]))

        instances = self.bcc.get_instance_types()
        self.bcc._make_get_request.assert_called_with("/api/get_instance_types")
        self.assertTrue(len(instances) == 1)


    def test_create_cluster(self):
        cluster_name = "Test cluster"
        password = 'password'
        cloud_type = '1'
        access_key = 'access_key'
        secret_key = 'secret_key'
        instance_type = '2'
        zone = 'zone'
        psscript = 'pss'
        wscript = 'ws'
        image_id = '3'

        launch_hash = {
                'cluster_name': cluster_name,
                'password': password,
                'cloud': cloud_type,
                'access_key': access_key,
                'secret_key': secret_key,
                'instance_type': instance_type,
                #'bucket_default': '',
                'post_start_script_url': psscript,
                'image_id': image_id
        }
        self.bcc._make_post_request = MagicMock(return_value=simplejson.dumps("Success"))

        result = self.bcc.create_cluster(cluster_name, password, cloud_type, access_key, secret_key, instance_type, placement=zone, post_start_script=psscript, worker_script=wscript, ami=image_id)
        
        self.bcc._make_post_request.assert_called_with("/api/launch", parameters=launch_hash)


