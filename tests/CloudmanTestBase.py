"""
Tests the functionality of the Blend CloudMan API. These tests require working
credentials to supported cloud infrastructure. 

Use ``nose`` to run these unit tests.
"""
import unittest
import os
from bioblend.cloudman.launch import Bunch
from bioblend.cloudman import CloudManConfig
from bioblend.cloudman import CloudManInstance

class CloudmanTestBase(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):        
        if os.environ.get('CLOUD_TYPE') == 'EC2':
            cls.access_key = 'AKIAIPOLBVMMPXZKLAWA'
            cls.secret_key = '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'
            cls.cluster_name = 'Blend CloudMan'
            cls.ami_id = 'ami-46d4792f'
            cls.instance_type = 'm1.small'
            cls.password = 'password'
            cls.cloud_metadata = Bunch(
                        id='1',  # for compatibility w/ DB representation
                        name="Amazon",
                        cloud_type="ec2",
                        bucket_default="cloudman",
                        region_name="us-east-1",
                        region_endpoint="ec2.amazonaws.com",
                        ec2_port="",
                        ec2_conn_path="/",
                        cidr_range="",
                        is_secure=True,
                        s3_host="s3.amazonaws.com",
                        s3_port="",
                        s3_conn_path='/',
                        )
        else:
            # Assume OpenStack/NeCTAR
            cls.access_key = '0103cea9ef094d9bab8d0ebdec654bf8'
            cls.secret_key = '73cad7184c2740fa9623eb1c6cec7c70'
            cls.cloud_metadata = Bunch(id = '-1',
                                  name = "NeCTAR",
                                  cloud_type='openstack',
                                  bucket_default='cloudman-os',
                                  region_name='NeCTAR',
                                  region_endpoint='nova.rc.nectar.org.au',
                                  ec2_port=8773,
                                  ec2_conn_path='/services/Cloud',
                                  cidr_range='115.146.92.0/22',
                                  is_secure=True,
                                  s3_host='swift.rc.nectar.org.au',
                                  s3_port=8888,
                                  s3_conn_path='/')
            cls.cluster_name = 'Blend CloudMan'
            cls.ami_id = 'ami-00000032'
            cls.instance_type = 'm1.small'
            cls.password = 'password'
    
    @classmethod
    def tearDownClass(cls):
        try:
            #TODO: cloudman's terminate method has a bug. Needs fix
            cls.cmi.terminate(delete_cluster=True)
        except:
            pass

 