"""
API for interacting with CloudMan.
"""
import requests
import simplejson

# API for interacting with CloudMan
class CloudMan:

    def __init__(self, url, password):
        """
        Create an instance of the CloudMan API class.

        The ``url`` is a string defining the address of CloudMan, for 
        example "http://127.0.0.1:42284". The ``password`` is CloudMan's password,
        as defined in the user data sent to CloudMan on instance creation.
        """
        self.cloudman_url = url
        self.password = password

    # Initialise CloudMan
    # type: The type of instance "Galaxy" (default), "Data", or "SGE"
    def initialize(self, type="Galaxy"):
        """
        Initialize CloudMan. This needs to be done before the cluster can be used.

        The ``type``, either 'Galaxy' (default), 'Data', or 'SGE', defines the type
        of cluster to initialize.
        """
        self._make_get_request("/cloud/initialize_cluster", parameters={'startup_opt': type})

    def get_status(self):
        """
        Get status information on CloudMan.
        """
        return simplejson.loads(self._make_get_request("/cloud/instance_state_json"))

    def get_nodes(self):
        """
        Get a list of nodes currently running in this CloudMan cluster.
        """
        instance_feed_json = self._make_get_request("/cloud/instance_feed_json")
        return simplejson.loads(instance_feed_json)['instances']

    def add_nodes(self, num_nodes):
        """
        Add worker nodes to the cluster.

        The ``num_nodes`` parameter defines the number of worker nodes to add.
        """
        payload = {'number_nodes' : num_nodes}
        result = self._make_get_request("/cloud/add_instances", parameters=payload)
        return result

    def remove_nodes(self, num_nodes, force=False):
        """
        Remove worker nodes from the cluster.

        The ``num_nodes`` parameter defines the number of worker nodes to remove.
        The ``force`` parameter (defaulting to False), is a boolean indicating 
        whether the nodes should be forcibly removed rather than gracefully removed.
        """
        payload = {'number_nodes': num_nodes, 'force_termination': force}
        result = self._make_get_request("/cloud/remove_instances", parameters=payload) 
        return result

    def remove_node(self, instance_id, force=False):
        """
        Remove a specific worker node from the cluster.

        The ``instance_id`` parameter defines the ID, as a string, of a worker node
        to remove from the cluster. The ``force`` parameter (defaulting to False), 
        is a boolean indicating whether the node should be forcibly removed rather 
        than gracefully removed.

        """
        payload = {'instance_id': instance_id}
        result = self._make_get_request("/cloud/remove_instance", parameters=payload) 

    def reboot_node(self, instance_id):
        """
        Reboot a specific worker node.

        The ``instance_id`` parameter defines the ID, as a string, of a worker node
        to reboot.
        """
        payload = {'instance_id': instance_id}
        result = self._make_get_request("/cloud/reboot_instance", parameters=payload) 

    def autoscaling_enabled(self):
        """
        Returns a boolean indicating whether autoscaling is enabled.
        """
        return bool(self.get_status()['autoscaling']['use_autoscaling'])

    def enable_autoscaling(self, minimum_nodes=0, maximum_nodes=19):
        """
        Enable cluster autoscaling, allowing the cluster to automatically add, or
        remove, worker nodes, as needed.

        The number of worker nodes in the cluster is bounded by the ``minimum_nodes``
        (default is 0) and ``maximum_nodes`` (default is 19) parameters.
        """
        if not(self.autoscaling_enabled()):
            payload = {'as_min': minimum_nodes, 'as_max': maximum_nodes}
            self._make_get_request("/cloud/toggle_autoscaling", parameters=payload)

    def disable_autoscaling(self):
        """
        Disable autoscaling, meaning that worker nodes will need to be manually
        added and removed.
        """
        if (self.autoscaling_enabled()):
            self._make_get_request("/cloud/toggle_autoscaling")

    def adjust_autoscaling(self, minimum_nodes=None, maximum_nodes=None):
        """
        Adjust the autoscaling configuration parameters.

        The number of worker nodes in the cluster is bounded by the optional ``minimum_nodes``
        (default is None) and ``maximum_nodes`` (default is None) parameters. If a parameter is not provided then its configuration value does not change.
        """
        if (self.autoscaling_enabled()):
            payload = {'as_min_adj': minimum_nodes, 'as_max_adj': maximum_nodes}
            self._make_get_request("/cloud/adjust_autoscaling", parameters=payload)

    def get_galaxy_state(self):
        """
        Get the current status of Galaxy running on the cluster.
        """
        payload = {'srvc': 'Galaxy'}
        status = self._make_get_request("/cloud/get_srvc_status", parameters=payload)
        return simplejson.loads(status)['status']

    def _make_get_request(self, url, parameters={}):
        """
        Private function that makes a GET request to the nominated ``url``, with the provided GET ``parameters``.
        """
        r = requests.get(self.cloudman_url + url, params=parameters, auth=("", self.password))
        return r.text
