# blend

A python library for interacting with BioCloudCentral, CloudMan, and Galaxy API 

# Usage

This section outlines how to use the *blend* API. 

## CloudMan

*blend* allows you to control [Galaxy Cloudman](http://usecloudman.org/).

Here is an example usage:

    # This connects to a locally running cloudman instance
    cm = cloudman.CloudMan("http://127.0.0.1:42284", "my password")

    # This tells CloudMan to initialize as a 'test' cluster
    cm.initialize(type="SGE")

    # Get the cluster status
    cluster_status = cm.get_status()

    # Get the list of current nodes in the cluster
    nodes = cm.get_nodes()

    # Add some nodes to the cluster
    cm.add_nodes(3)

    # Remove some nodes from the cluster
    cm.remove_nodes(2, force=False)

    # Reboot a particular instance
    cm.reboot_node("my_instance_id")

    # Remove a particular instance
    cm.remove_node("my instance id", force=True)

    # Enable autoscaling
    cm.enable_autoscaling(minimum_nodes=0,maximum_nodes=19)

    # Adjust autoscaling
    cm.adjust_autoscaling(minimum_nodes=5, maximum_nodes=10)

    # Disable autoscaling
    cm.disable_autoscaling()

    # If your cluster is running Galaxy, then you can get the state of Galaxy from CloudMan
    galaxy_state = cm.get_galaxy_state()


The unit tests in the `tests` folder also provide usage examples.


## Galaxy

*Coming soon...*

# Testing

The unit tests, in the `tests` folder, can be run using [nose](https://github.com/nose-devs/nose). From the project root:

    nosetests
