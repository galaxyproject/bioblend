import re
import simplejson
from blend import bcc


url = "http://127.0.0.1:8000"
access_key = 'access_key'
secret_key = 'secret_key'
bcc = bcc.BCC(url)

clouds = bcc.get_clouds()
cloud_name = clouds[1]['name']
cloud_type = clouds[1]['cloud_type']

images = bcc.get_images()
image_id = images[2]['id']

instance_types = bcc.get_instance_types()
instance_type = instance_types[-1]['tech_name']

regions = bcc.get_regions(cloud_name, access_key, secret_key, instance_type)
region = regions[0]

cluster_name = "My cluster"
password = 'password'

psscript = ''
wscript = ''

user_data = {
        'cluster_name': 'Test Cluster',
        'password': 'password',
        'cloud_type': cloud_type,
        'access_key': access_key,
        'secret_key': secret_key,
        'instance_type': instance_type,
        'image_id': image_id
        }

result = bcc.launch(instance_type, ud=user_data, cloud_name=cloud_name)
print result
