import requests
import simplejson

# API for interacting with CloudMan
class CloudMan:

    # Constructor
    # url: The URL of CloudMan
    # password: The password for CloudMan
    def __init__(self, url, password):
        self.cloudman_url = url
        self.password = password

    # Initialise CloudMan
    # type: The type of instance .....
    # storage_size: .....
    def initialize(self, type="some size", storage_size="some other size"):
        print "Initializing with type:{0} and storage_size:{1}".format(type, storage_size)

    # Get the current status of Cloudman as JSON
    def get_status(self):
        return simplejson.loads(self._make_get_request("/cloud/instance_state_json"))

    # Get a list of current CloudMan nodes
    def get_nodes(self):
        instance_feed_json = self._make_get_request("/cloud/instance_feed_json")
        return simplejson.loads(instance_feed_json)['instances']

    def add_nodes(self, num_nodes, type="some size", spot_price="some price"):
        payload = {'number_nodes' : num_nodes}
        result = self._make_get_request("/cloud/add_instances", parameters=payload)
        return result

    def remove_nodes(self, num_nodes, force=False):
        payload = {'number_nodes': num_nodes, 'force_termination': force}
        result = self._make_get_request("/cloud/remove_instances", parameters=payload) 
        return result

    def remove_node(self, instance_id, force=False):
        payload = {'instance_id': instance_id}
        result = self._make_get_request("/cloud/remove_instance", parameters=payload) 

    def reboot_node(self, instance_id):
        payload = {'instance_id': instance_id}
        result = self._make_get_request("/cloud/reboot_instance", parameters=payload) 

    def autoscaling_enabled(self):
        return bool(self.get_status()['autoscaling']['use_autoscaling'])

    def enable_autoscaling(self, minimum_nodes=0, maximum_nodes=19):
        if not(self.autoscaling_enabled()):
            payload = {'as_min': minimum_nodes, 'as_max': maximum_nodes}
            self._make_get_request("/cloud/toggle_autoscaling", parameters=payload)

    def disable_autoscaling(self):
        if (self.autoscaling_enabled()):
            self._make_get_request("/cloud/toggle_autoscaling")

    def adjust_autoscaling(self, minimum_nodes=None, maximum_nodes=None):
        if (self.autoscaling_enabled()):
            payload = {'as_min_adj': minimum_nodes, 'as_max_adj': maximum_nodes}
            self._make_get_request("/cloud/adjust_autoscaling", parameters=payload)

    def get_galaxy_state(self):
        payload = {'srvc': 'Galaxy'}
        status = self._make_get_request("/cloud/get_srvc_status", parameters=payload)
        return simplejson.loads(status)['status']

    def _make_get_request(self, url, parameters={}):
        r = requests.get(self.cloudman_url + url, params=parameters, auth=("", self.password))
        return r.text
