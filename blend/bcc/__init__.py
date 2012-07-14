import simplejson
import requests


class BCC:
    def __init__(self, url):
        """
        Create an instance of the BioCloudCentral API class.

        The ``url`` is a string defining the address of BioCloudCentral, for
        example "https://biocloudcentral.herokuapp.com".
        """
        self.biocloudcentral_url = url

    def get_clouds(self):
        """
        Get a list of cloud types supported by BioCloudCentral.
        """
        return simplejson.loads(self._make_get_request("/api/get_clouds"))

    def get_images(self):
        """
        Get a list of images supported by BioCloudCentral.
        """
        return simplejson.loads(self._make_get_request("/api/get_images"))

    def get_instance_types(self):
        """
        Get a list of instance types (flavors) supported by BioCloudCentral.
        """
        return simplejson.loads(self._make_get_request("/api/get_instance_types"))

    def get_regions(self, cloud_name, access_key, secret_key, instance_type):
        params = {
                'cloud_name': cloud_name,
                'access_key': access_key,
                'secret_key': secret_key,
                'instance_type': instance_type
                }
        return simplejson.loads(self._make_get_request("/api/get_regions", parameters=params))

    def get_instance_state(self, secret_key, access_key, cloud_type, instance_id):
        """
        """
        parameters = {
                'access_key': access_key,
                'secret_key': secret_key,
                'cloud_type': cloud_type,
                'instance_id': instance_id
                }
        return simplejson.loads(self._make_get_request("/api/state", parameters=parameters))

    def launch(self, instance_type, ud={}, cloud_name="Amazon"):
        """
        Launch a new CloudMan cluster.

        The ``instance_type`` is the ``tech_name`` (e.g. ``m1.small``) for
        the master instance of the cluster (from ``get_instance_types()``).

        The ``ud`` is a dictionary of user data. It should at least contain
        ``cluster_name``, ``password``, ``cloud``, ``access_key``, ``secret_key``,
        ``instance_type``, and ``image_id``.

        The ``cloud_name``, defaulting to ``Amazon``, is the name of the cloud.

        """
        parameters = {
                'cluster_name': ud['cluster_name'],
                'password': ud['password'],
                'cloud': ud['cloud_type'],
                'access_key': ud['access_key'],
                'secret_key': ud['secret_key'],
                'instance_type': instance_type,
                #'post_start_script_url': post_start_script,
                'image_id': ud['image_id'],
        }
        return self._make_post_request("/api/launch", parameters=parameters)

    def _make_get_request(self, url, parameters={}):
        """
        Private function that makes a GET request to the nominated ``url``, with the provided GET ``parameters``.
        """
        r = requests.get(self.biocloudcentral_url + url, params=parameters)
        return r.text

    def _make_post_request(self, url, parameters={}):
        """
        Private function that makes a POST request to the nominated ``url``, with the provides POST ``parameters``.
        """
        r = requests.post(self.biocloudcentral_url + url, data=parameters)
        return r.text
