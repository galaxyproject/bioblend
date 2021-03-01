"""
Tests the functionality of the Blend CloudMan API. These tests require working
credentials to supported cloud infrastructure.
"""
import os
import unittest

from bioblend.util import Bunch
from . import test_util


class CloudmanTestBase(unittest.TestCase):

    @classmethod
    @test_util.skip_unless_cloudman()
    def setUpClass(cls):
        if os.environ.get('BIOBLEND_CLOUD_TYPE') == 'EC2':
            cls.access_key = os.environ['BIOBLEND_ACCESS_KEY']
            cls.secret_key = os.environ['BIOBLEND_SECRET_KEY']
            cls.cluster_name = 'Blend CloudMan'
            cls.ami_id = os.environ['BIOBLEND_AMI_ID']
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
                s3_conn_path='/')
        else:
            # Assume OpenStack/NeCTAR
            cls.access_key = os.environ['BIOBLEND_ACCESS_KEY']
            cls.secret_key = os.environ['BIOBLEND_SECRET_KEY']
            cls.cloud_metadata = Bunch(
                id='-1',
                name="NeCTAR",
                cloud_type='openstack',
                bucket_default='cloudman-os',
                region_name='melbourne',
                region_endpoint='nova.rc.nectar.org.au',
                ec2_port=8773,
                ec2_conn_path='/services/Cloud',
                cidr_range='115.146.92.0/22',
                is_secure=True,
                s3_host='swift.rc.nectar.org.au',
                s3_port=8888,
                s3_conn_path='/')
            cls.cluster_name = 'Blend CloudMan'
            cls.ami_id = os.environ['BIOBLEND_AMI_ID']
            cls.instance_type = 'm1.small'
            cls.password = 'password'

    @classmethod
    @test_util.skip_unless_cloudman()
    def tearDownClass(cls):
        try:
            # TODO: cloudman's terminate method has a bug. Needs fix
            cls.cmi.terminate(delete_cluster=True)
        except Exception:
            pass
