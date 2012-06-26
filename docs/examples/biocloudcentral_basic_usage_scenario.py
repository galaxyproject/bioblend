import re
import simplejson
from blend import bcc

# URL of BioCloudCentral
url = "http://127.0.0.1:8000"

# Ec2 credentials
access_key = 'access_key'
secret_key = 'secret_key'

# Create a BioCloudCentral connection
bcc = bcc.BCC(url)

# Get the supported clouds
clouds = bcc.get_clouds()
cloud_name = clouds[1]['name']
cloud_type = clouds[1]['cloud_type']

# Get the supported machine images
images = bcc.get_images()
image_id = images[2]['id']

# Get the supported instance types
instance_types = bcc.get_instance_types()
instance_type = instance_types[-1]['tech_name']

# Get the supported regions for the cloud and instance type
regions = bcc.get_regions(cloud_name, access_key, secret_key, instance_type)
region = regions[0]

cluster_name = "My cluster"
password = 'password'

# Create the user data object
user_data = {
        'cluster_name': cluster_name,
        'password': password,
        'cloud_type': cloud_type,
        'access_key': access_key,
        'secret_key': secret_key,
        'instance_type': instance_type,
        'image_id': image_id
        }

# Launch an instance
result = bcc.launch(instance_type, ud=user_data, cloud_name=cloud_name)
print result
