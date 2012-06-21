#import requests
import re
import simplejson
from blend import biocloudcentral


url = "http://127.0.0.1:8000"
bcc = biocloudcentral.BioCloudCentral(url)

cloud_types = bcc.get_cloud_types()
cloud_id = cloud_types[1]['id']

images = bcc.get_images()
image_id = images[2]['id']

instance_types = bcc.get_instance_types()
instance_type_id = instance_types[-1]['tech_name']

cluster_name = "My cluster"
password = 'password'
access_key = 'access_key'
secret_key = 'secret_key'
zone = ''
psscript = ''
wscript = ''

result = bcc.create_cluster(cluster_name, password, cloud_id, access_key, secret_key, instance_type_id, placement=zone, post_start_script=psscript, worker_script=wscript, ami=image_id)
print result
