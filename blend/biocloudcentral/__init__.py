import simplejson
import requests

class BioCloudCentral:
    def __init__(self, url):
        """
        Create an instance of the BioCloudCentral API class.

        The ``url`` is a string defining the address of BioCloudCentral, for
        example "https://biocloudcentral.herokuapp.com".
        """
        self.biocloudcentral_url = url


    def get_cloud_types(self):
        """
        Get a list of cloud types supported by BioCloudCentral.
        """
        return simplejson.loads(self._make_get_request("/api/get_cloud_types"))


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

    def create_cluster(self, cluster_name, password, cloud_type, access_key, secret_key, instance_type, placement=None, post_start_script=None, worker_script=None, ami=None):
        """
        Launch a new CloudMan cluster.

        The ``cluster_name`` names the cluster. The ``password`` sets the 
        user password for web access to CloudMan (their is no username). The 
        ``cloud_type`` is the numerical ID of the cloud to deploy (the ``id`` field 
        from ``get_cloud_types()``). The ``access_key`` and ``secret_key`` are 
        your cloud access credentials (BioCloudCentral requires these to create the cluster). The ``instance_type`` is the ``tech_name`` (e.g. ``m1.small``) for
        the master instance of the cluster (from ``get_instance_types()``).

        The ``placement`` defines the zone for the cluster. The
        ``post_start_script`` defines the post start script. The ``worker_script``
        defines the worker script. The ``ami`` defines the numerical ID of
        the image to use for the master instance of the cluster (``id`` field
        from ``get_images()``).
        """
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
        """
        Private function that makes a POST request to the nominated ``url``, with the provides POST ``parameters``.
        """
        r = requests.post(self.biocloudcentral_url + url, data=parameters)
        return r.text
