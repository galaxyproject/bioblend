import simplejson
import requests

class BioCloudCentral:
    def __init__(self, url):
        self.biocloudcentral_url = url


    def get_cloud_types(self):
        return simplejson.loads(self._make_get_request("/api/get_cloud_types"))


    def get_images(self):
        return simplejson.loads(self._make_get_request("/api/get_images"))


    def get_instance_types(self):
        return simplejson.loads(self._make_get_request("/api/get_instance_types"))

    def create_cluster(self, cluster_name, password, cloud_type, access_key, secret_key, instance_type, placement=None, post_start_script=None, worker_script=None, ami=None):
        parameters = {
                'cluster_name': cluster_name,
                'password': password,
                'cloud': cloud_type,
                'access_key': access_key,
                'secret_key': secret_key,
                'instance_type': instance_type,
                'post_start_script_url': post_start_script,
                'image_id': ami
        }
        return self._make_post_request("/api/launch", parameters=parameters)


    def _make_get_request(self, url, parameters={}):
        """
        Private function that makes a GET request to the nominated ``url``, with the provided GET ``parameters``.
        """
        r = requests.get(self.biocloudcentral_url + url, params=parameters)
        return r.text

    def _make_post_request(self, url, parameters={}):
        r = requests.post(self.biocloudcentral_url + url, data=parameters)
        return r.text
