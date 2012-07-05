"""
A quick way to start and initialize an instance of the CloudMan platform 
directly from the command line.

Usage:
python start_cloudman.py <cluster_name> <password> <cm_type> <instance_type> <AMI> <access_key> <secret_key>

<cm_type> can be 'Galaxy', 'Data', or 'SGE'
(see http://wiki.g2.bx.psu.edu/CloudMan, Step 3 for more details on types)

Example:
python start_cloudman.py "cluster x" pwd SGE m1.small ami-00000032 <access_key> <secret_key>
"""
import sys
import time

from blend.cloudman import CloudMan
from blend.cloudman.launch import Bunch
from blend.cloudman.launch import CloudManLaunch

def start_cloudman(name, pwd, cm_type, inst_type, ami, ak, sk):
    """
    Start an instance of CloudMan with the provided arguments.
    Returns a tuple: an instance of ``CloudManLaunch`` pointing to the class
    instance used to launch this CloudMan; and an instance of ``CloudMan``
    pointing to the given instance of CloudMan.
    """
    cloud = None # If left as None, Blend will default to Amazon
    # Define properties for the NeCTAR cloud
    cloud = Bunch(id = '-1',
                  name = "NeCTAR",
                  cloud_type='openstack',
                  bucket_default='cloudman-os',
                  region_name='NeCTAR',
                  region_endpoint='nova.rc.nectar.org.au',
                  ec2_port=8773,
                  ec2_conn_path='/services/Cloud',
                  cidr_range='115.146.92.0/22',
                  is_secure=False,
                  s3_host='swift.rc.nectar.org.au',
                  s3_port=8888,
                  s3_conn_path='/')
    # Create an instance of the CloudManLaunch class and launch a CloudMan instance
    cml = CloudManLaunch(ak, sk, cloud)
    cml.launch(name, ami, inst_type, pwd)
    s = cml.get_status()
    # Wait until he have an IP (i.e., CloudMan is ready)
    while s['public_ip'] == '':
        print "Instance not ready yet (it's in state '{0}'); waiting..."\
                .format(s['instance_state'])
        time.sleep(5)
        s = cml.get_status()
        if s['error'] != '':
            print "Error launching an instance: {0}".format(s['error'])
            sys.exit(1)
    print "Instance booted; configuring CloudMan as '{0}' type".format(cm_type)
    # Configure the CloudMan platform type
    cm = CloudMan(s['public_ip'], pwd)
    cm.initialize(cm_type)
    cm.get_status()
    print "Done! CloudMan IP is {0}/cloud".format(s['public_ip'])
    return cml, cm

if __name__=="__main__":
    if len(sys.argv) != 8:
        print "\nUsage:\n"\
            "python start_cloudman.py <cluster_name> <password> <cm_type> "\
            "<instance_type> <AMI> <access_key> <secret_key>"
        sys.exit(1)
    cml, cm = start_cloudman(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4],
            sys.argv[5], sys.argv[6], sys.argv[7])
