import requests
import simplejson

class CloudMan:

    def __init__(self, url, password):
        self.cloudman_url = url
        self.password = password

    def initialize(self, type="some size", storage_size="some other size"):
        print "Initializing with type:{0} and storage_size:{1}".format(type, storage_size)

    def get_status(self):
        print "Get status"
        return self._make_get_request("/cloud/instance_state_json")

    def get_nodes(self):
        print "Get nodes"
        instance_feed_json = self._make_get_request("/cloud/instance_feed_json")
        return simplejson.loads(instance_feed_json)['instances']

    def add_nodes(self, num_nodes, type="some size", spot_price="some price"):
        print "Add nodes"
        payload = {'number_nodes' : num_nodes}
        result = self._make_get_request("/cloud/add_instances", parameters=payload)
        return result

    def remove_nodes(self, num_nodes, force=False):
        print "Remove nodes"
        payload = {'number_nodes': num_nodes, 'force_termination': force}
        result = self._make_get_request("/cloud/remove_instances", parameters=payload) 
        return result

    def remove_node(self, instance_id, force=False):
        print "Remove node"


    def reboot_node(self, instance_id):
        print "Reboot node"

    def enable_autoscaling(self, minimum_nodes=0, maximum_nodes=19):
        print "Enable autoscaling"

    def disable_autoscaling(self):
        print "Disable autoscaling"

    def adjust_autoscaling(self, minimum_nodes=None, maximum_nodes=None):
        print "Adjust autoscaling"

    def get_galaxy_state(self):
        print "Get Galaxy state"
        return "Some state"

    def _make_get_request(self, url, parameters={}):
       r = requests.get(self.cloudman_url + url, params=parameters, auth=("", self.password))
       return r.text

