"""
A quick way to start and initialize an instance of the CloudMan platform
directly from the command line.

Usage::

  python start_cloudman.py <cluster_name> <password> <cm_type> <instance_type> <AMI> <access_key> <secret_key>

``<cm_type>`` can be 'Galaxy', 'Data', or 'SGE'
(see https://galaxyproject.org/cloudman/ for more details on types)

Example:
python start_cloudman.py "cluster bioblend" pwd SGE m1.small ami-00000032 <access_key> <secret_key>
"""

import sys

from bioblend.cloudman import CloudManConfig, CloudManInstance
from bioblend.util import Bunch


def start_cloudman(name, pwd, cm_type, inst_type, ami, ak, sk):
    """
    Start an instance of CloudMan with the provided arguments.

    Returns a tuple: an instance of ``CloudManConfig`` pointing to the
    settings used to launch this instance of CloudMan; and an instance
    of ``CloudManInstance`` pointing to the given instance of CloudMan.
    """
    cloud = None  # If left as None, BioBlend will default to Amazon
    # Define properties for the NeCTAR cloud
    cloud = Bunch(id='-1',
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
    # Create an instance of the CloudManConfig class and launch a CloudMan instance
    cmc = CloudManConfig(
        ak, sk, name, ami, inst_type, pwd, cloud_metadata=cloud,
        cloudman_type=cm_type, initial_storage_size=2, placement='melbourne-np')
    print("Configured an instance; waiting to launch and boot...")
    cmi = CloudManInstance.launch_instance(cmc)
    print(f"Done! CloudMan IP is {cmi.cloudman_url}")
    return cmc, cmi


if __name__ == "__main__":
    if len(sys.argv) != 8:
        print("\nUsage:\n"
              "python start_cloudman.py <cluster_name> <password> <cm_type> "
              "<instance_type> <AMI> <access_key> <secret_key>")
        sys.exit(1)
    cml, cm = start_cloudman(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4],
                             sys.argv[5], sys.argv[6], sys.argv[7])
