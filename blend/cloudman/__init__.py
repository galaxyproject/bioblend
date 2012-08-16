"""
API for interacting with a CloudMan instance.
"""
import requests
import simplejson
from urlparse import urlparse


class CloudMan:

    def __init__(self, url, password):
        """
        Create an instance of the CloudMan API class, which is to be used when
        manipulating that given CloudMan instance.

        The ``url`` is a string defining the address of CloudMan, for
        example "http://115.146.92.174". The ``password`` is CloudMan's password,
        as defined in the user data sent to CloudMan on instance creation.
        """
        # Make sure the url scheme is defined (otherwise requests will not work)
        if not urlparse(url).scheme:
            url = "http://" + url
        self.cloudman_url = url
        self.password = password

    def __repr__(self):
        return "CloudMan instance at {0}/cloud".format(self.cloudman_url)

    def initialize(self, type="Galaxy"):
        """
        Initialize CloudMan platform. This needs to be done before the cluster
        can be used.

        The ``type``, either 'Galaxy' (default), 'Data', or 'SGE', defines the type
        of cluster platform to initialize.
        """
        self._make_get_request("/cloud/initialize_cluster", parameters={'startup_opt': type})

    def get_cluster_type(self):
        """
        Get the ``type`` this CloudMan cluster has been initialized to. See the
        CloudMan docs about the available types. If the cluster has not yet been
        initialized, this method returns ``None``.
        """
        return self._make_get_request("/cloud/get_cluster_type")

    def get_status(self):
        """
        Get status information on this CloudMan instance.
        """
        return self._make_get_request("/cloud/instance_state_json")

    def get_nodes(self):
        """
        Get a list of nodes currently running in this CloudMan cluster.
        """
        instance_feed_json = self._make_get_request("/cloud/instance_feed_json")
        return simplejson.loads(instance_feed_json)['instances']

    def get_cluster_size(self):
        """
        Get the size of the cluster in terms of the number of nodes; this count
        includes the master node.
        """
        return len(self.get_nodes())

    def add_nodes(self, num_nodes, instance_type='', spot_price=''):
        """
        Add a number of worker nodes to the cluster, optionally specifying
        the type for new instances. If ``instance_type`` is not specified,
        instance(s) of the same type as the master instance will be started.
        Note that the ``instance_type`` must match the type of instance
        available on the given cloud.

        ``spot_price`` applies only to AWS and, if set, defines the maximum
        price for Spot instances, thus turning this request for more instances
        into a Spot request.
        """
        payload = {'number_nodes': num_nodes,
                   'instance_type': instance_type,
                   'spot_price': spot_price}
        return self._make_get_request("/cloud/add_instances", parameters=payload)

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
        return self._make_get_request("/cloud/remove_instance", parameters=payload)

    def reboot_node(self, instance_id):
        """
        Reboot a specific worker node.

        The ``instance_id`` parameter defines the ID, as a string, of a worker node
        to reboot.
        """
        payload = {'instance_id': instance_id}
        return self._make_get_request("/cloud/reboot_instance", parameters=payload)

    def autoscaling_enabled(self):
        """
        Returns a boolean indicating whether autoscaling is enabled.
        """
        return bool(self.get_status()['autoscaling']['use_autoscaling'])

    def enable_autoscaling(self, minimum_nodes=0, maximum_nodes=19):
        """
        Enable cluster autoscaling, allowing the cluster to automatically add,
        or remove, worker nodes, as needed.

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

        The number of worker nodes in the cluster is bounded by the optional
        ``minimum_nodes`` and ``maximum_nodes`` parameters. If a parameter is
        not provided then its configuration value does not change.
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

    def terminate(self, terminate_master_instance=True, delete_cluster=False):
        """
        Terminate this CloudMan cluster. Ther is an option to also terminate the
        master instance (all worker instances will be terminated in the process
        of cluster termination), and deletete the whole cluster.

        .. note::
            Deleting a cluster is irreverisble - all of the data will be
            permatently deleted.
        """
        payload = {'terminate_master_instance': terminate_master_instance,
                   'delete_cluster': delete_cluster}
        result = self._make_get_request("/cloud/kill_all", parameters=payload,
                timeout=15)
        return result

    def _make_get_request(self, url, parameters={}, timeout=None):
        """
        Private function that makes a GET request to the nominated ``url``,
        with the provided GET ``parameters``. Optionally, set the ``timeout``
        to stop waiting for a reponse after a given number of seconds. This is
        particularly useful when terminating a cluster as it may terminate
        before sending a reponse.
        """
        r = requests.get(self.cloudman_url + url, params=parameters,
                auth=("", self.password), timeout=timeout)
        return r.text
