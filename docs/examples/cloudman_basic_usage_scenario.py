from bioblend import cloudman

url = "http://127.0.0.1:42284"
password = "password"
cm = cloudman.CloudManInstance(url, password)

# Expects CloudMan to be running locally
# Set cluster type and storage size
cm.initialize(type="SGE")

# Get cluster status
status = cm.get_status()

# Get nodes
nodes = cm.get_nodes()
# There should be a master node

# Add node
num_nodes = 1
status = cm.add_nodes(num_nodes)

# Remove nodes
status = cm.remove_nodes(num_nodes, force=True)

instance_id = "abcdef"
cm.remove_node(instance_id, force=True)

# Reboot instance
cm.reboot_node(instance_id)

# Autoscaling:
# enable
cm.disable_autoscaling()
cm.enable_autoscaling(minimum_nodes=0, maximum_nodes=19)

# autoscaling should be enabled now
is_enabled = cm.autoscaling_enabled()

min_autoscaling = cm.get_status()['autoscaling']['as_min']
max_autoscaling = cm.get_status()['autoscaling']['as_max']

# adjust
cm.adjust_autoscaling(minimum_nodes=5, maximum_nodes=10)

# disable
cm.disable_autoscaling()

# autoscaling should be disabled
cm.autoscaling_enabled()

# Get Galaxy DNS/Host
galaxy_state = cm.get_galaxy_state()  # RUNNING, STARTING.....
