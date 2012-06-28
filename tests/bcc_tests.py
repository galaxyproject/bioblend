"""
Tests the functionality of the Blend BioCloudCentral API, without actually 
making calls to a remote BioCloudCentral instance/server. These don't 
actually ensure that Blend is integrated with BioCloudCentral correctly. 
They only ensure that if you refactor the Blend BioCloudCentral API code, 
that it will maintain its current behavior.

Use ``nose`` to run these unit tests.
"""
import unittest
from mock import MagicMock
from blend import bcc
import simplejson

class BCCTest(unittest.TestCase):
    def setUp(self):
        url = "http://127.0.0.1:8000"
        self.bcc = bcc.BCC(url)

    def test_get_clouds(self):
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

        clouds = self.bcc.get_clouds()
        self.bcc._make_get_request.assert_called_with("/api/get_clouds")
        self.assertTrue(len(clouds) == 1)


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


    def test_get_regions(self):
        region_hash = {
                'name': 'a_region'
        }
        self.bcc._make_get_request = MagicMock(return_value=simplejson.dumps([region_hash]))

        regions = self.bcc.get_regions('cloud_name', 'access_key', 'secret_key', 'instance_type')
        params = {
                'cloud_name': 'cloud_name',
                'access_key': 'access_key',
                'secret_key': 'secret_key',
                'instance_type': 'instance_type'
                }
        self.bcc._make_get_request.assert_called_with("/api/get_regions", parameters=params)
        self.assertTrue(len(regions) == 1)



    def test_launch(self):
        cluster_name = "Test cluster"
        password = 'password'
        cloud_name = 'Amazon'
        access_key = 'access_key'
        secret_key = 'secret_key'
        instance_type = 'm1.small'
        zone = 'zone'
        psscript = 'pss'
        wscript = 'ws'
        image_id = 'ami-00000001'

        launch_hash = {
                'cluster_name': cluster_name,
                'password': password,
                'cloud': cloud_name,
                'access_key': access_key,
                'secret_key': secret_key,
                'instance_type': instance_type,
                #'bucket_default': '',
                #'post_start_script_url': psscript,
                'image_id': image_id
        }
        self.bcc._make_post_request = MagicMock(return_value=simplejson.dumps("Success"))

        user_data = {
                'access_key': access_key,
                'secret_key': secret_key,
                'cluster_name': cluster_name,
                'cloud_type': cloud_name,
                'freenxpass':'',
                'password': password,
                's3_port': '',
                'region_name': zone,
                'cidr_range': '',
                'region_endpoint': '',
                'ec2_port': '',
                'bucket_default': '',
                's3_host': '',
                'is_secure': 'False',
                's3_conn_path': '/',
                'ec2_conn_path': '/services/Cloud',
                'image_id': image_id
        }
        result = self.bcc.launch(instance_type, ud=user_data, cloud_name=cloud_name)

        self.bcc._make_post_request.assert_called_with("/api/launch", parameters=launch_hash)
