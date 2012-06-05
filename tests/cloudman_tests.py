from blend import cloudman

# Some ad-hoc tests for the CloudMan API
# Expects CloudMan to be running locally
# This needs to be converted to proper unit tests

## Start master
##cluster = cloudman.StartCluster
##cluster.ip

url = "http://127.0.0.1:42284"
password = "password"

cm = cloudman.CloudMan(url, password)
## Master is running

## Configure Master

## Set cluster type and storage size
cm.initialize(type="xxx", storage_size="yyy")
##cm.set_cluster_type(type=xxx,storage_size=xxx)
##cm.configure(type=xxx,

## Get cluster status
status_object = cm.get_status()
print status_object

## Get nodes
list_of_nodes = cm.get_nodes()
print list_of_nodes

## Add node
num_nodes = 10
list_of_nodes = cm.add_nodes(num_nodes, type="xxx", spot_price="yyy")
print list_of_nodes

## Remove nodes
instance_id = "abcdef"
list_of_removed_nodes = cm.remove_nodes(num_nodes, force=True)
print list_of_nodes
cm.remove_node(instance_id, force=True)

## Reboot instance
cm.reboot_node(instance_id)

## Autoscaling
cm.enable_autoscaling(minimum_nodes=0,maximum_nodes=19) #20 is max on AWS
cm.disable_autoscaling()
cm.adjust_autoscaling(minimum_nodes=None,maximum_nodes=None)

## Get Galaxy DNS/Host
galaxy_state = cm.get_galaxy_state() #RUNNING, STARTING.....
##galaxy_host = cm.get_galaxy_dns()


## Restart cluster

## Administration
## reboot master
## reboot service
## update galaxy


