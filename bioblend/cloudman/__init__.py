"""
API for interacting with a CloudMan instance.
"""
import functools
import json
import time
from urllib.parse import urlparse

import requests

import bioblend
from bioblend.cloudman.launch import CloudManLauncher
from bioblend.util import Bunch


def block_until_vm_ready(func):
    """
    This decorator exists to make sure that a launched VM is
    ready and has received a public IP before allowing the wrapped
    function call to continue. If the VM is not ready, the function will
    block until the VM is ready. If the VM does not become ready
    until the vm_ready_timeout elapses or the VM status returns an error,
    a VMLaunchException will be thrown.

    This decorator relies on the wait_until_instance_ready method defined in
    class GenericVMInstance. All methods to which this decorator is applied
    must be members of a class which inherit from GenericVMInstance.

    The following two optional keyword arguments are recognized by this decorator:

    :type vm_ready_timeout: int
    :param vm_ready_timeout: Maximum length of time to block before timing out.
                             Once the timeout is reached, a VMLaunchException
                             will be thrown.

    :type vm_ready_check_interval: int
    :param vm_ready_check_interval: The number of seconds to pause between consecutive
                                    calls when polling the VM's ready status.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        obj = args[0]
        timeout = kwargs.pop('vm_ready_timeout', 300)
        interval = kwargs.pop('vm_ready_check_interval', 10)
        try:
            obj.wait_until_instance_ready(timeout, interval)
        except AttributeError:
            raise VMLaunchException("Decorated object does not define a wait_until_instance_ready method."
                                    "Make sure that the object is of type GenericVMInstance.")
        return func(*args, **kwargs)
    return wrapper


class VMLaunchException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class CloudManConfig:

    def __init__(self,
                 access_key=None,
                 secret_key=None,
                 cluster_name=None,
                 image_id=None,
                 instance_type='m1.medium',
                 password=None,
                 cloud_metadata=None,
                 cluster_type=None,
                 galaxy_data_option='',
                 initial_storage_size=10,
                 key_name='cloudman_key_pair',
                 security_groups=None,
                 placement='',
                 kernel_id=None,
                 ramdisk_id=None,
                 block_until_ready=False,
                 **kwargs):
        """
        Initializes a CloudMan launch configuration object.

        :type access_key: str
        :param access_key: Access credentials.

        :type secret_key: str
        :param secret_key: Access credentials.

        :type cluster_name: str
        :param cluster_name: Name used to identify this CloudMan cluster.

        :type image_id: str
        :param image_id: Machine image ID to use when launching this
                         CloudMan instance.

        :type instance_type: str
        :param instance_type: The type of the machine instance, as understood by
                              the chosen cloud provider. (e.g., ``m1.medium``)

        :type password: str
        :param password: The administrative password for this CloudMan instance.

        :type cloud_metadata: Bunch
        :param cloud_metadata: This object must define the properties required
                               to establish a `boto <https://github.com/boto/boto/>`_
                               connection to that cloud. See this method's implementation
                               for an example of the required fields. Note that as
                               long the as provided object defines the required fields,
                               it can really by implemented as anything (e.g.,
                               a Bunch, a database object, a custom class). If no
                               value for the ``cloud`` argument is provided, the
                               default is to use the Amazon cloud.

        :type kernel_id: str
        :param kernel_id: The ID of the kernel with which to launch the
                          instances

        :type ramdisk_id: str
        :param ramdisk_id: The ID of the RAM disk with which to launch the
                           instances

        :type key_name: str
        :param key_name: The name of the key pair with which to launch instances

        :type security_groups: list of str
        :param security_groups: The IDs of the security groups with which to
                                associate instances

        :type placement: str
        :param placement: The availability zone in which to launch the instances

        :type cluster_type: str
        :param cluster_type: The ``type``, either 'Galaxy', 'Data', or
                             'Test', defines the type of cluster platform to initialize.

        :type galaxy_data_option: str
        :param galaxy_data_option: The storage type to use for this instance.
                             May be 'transient', 'custom_size' or ''. The default is '',
                             which will result in ignoring the bioblend specified
                             initial_storage_size. 'custom_size' must be used for
                             initial_storage_size to come into effect.

        :type initial_storage_size: int
        :param initial_storage_size: The initial storage to allocate for the instance.
                                     This only applies if ``cluster_type`` is set
                                     to either ``Galaxy`` or ``Data`` and ``galaxy_data_option``
                                     is set to ``custom_size``

        :type block_until_ready: bool
        :param block_until_ready: Specifies whether the launch method will block
                                 until the instance is ready and only return once
                                 all initialization is complete. The default is False.
                                 If False, the launch method will return immediately
                                 without blocking. However, any subsequent calls
                                 made will automatically block if the instance is
                                 not ready and initialized. The blocking timeout
                                 and polling interval can be configured by providing
                                 extra parameters to the ``CloudManInstance.launch_instance``
                                 method.
        """
        if security_groups is None:
            security_groups = ['CloudMan']
        self.set_connection_parameters(access_key, secret_key, cloud_metadata)
        self.set_pre_launch_parameters(
            cluster_name, image_id, instance_type,
            password, kernel_id, ramdisk_id, key_name, security_groups,
            placement, block_until_ready)
        self.set_post_launch_parameters(cluster_type, galaxy_data_option, initial_storage_size)
        self.set_extra_parameters(**kwargs)

    def set_connection_parameters(self, access_key, secret_key, cloud_metadata=None):
        self.access_key = access_key
        self.secret_key = secret_key
        self.cloud_metadata = cloud_metadata

    def set_pre_launch_parameters(
            self, cluster_name, image_id, instance_type, password,
            kernel_id=None, ramdisk_id=None, key_name='cloudman_key_pair',
            security_groups=None, placement='', block_until_ready=False):
        if security_groups is None:
            security_groups = ['CloudMan']
        self.cluster_name = cluster_name
        self.image_id = image_id
        self.instance_type = instance_type
        self.password = password
        self.kernel_id = kernel_id
        self.ramdisk_id = ramdisk_id
        self.key_name = key_name
        self.security_groups = security_groups
        self.placement = placement
        self.block_until_ready = block_until_ready

    def set_post_launch_parameters(self, cluster_type=None, galaxy_data_option='', initial_storage_size=10):
        self.cluster_type = cluster_type
        self.galaxy_data_option = galaxy_data_option
        self.initial_storage_size = initial_storage_size

    def set_extra_parameters(self, **kwargs):
        self.kwargs = kwargs

    class CustomTypeEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, (CloudManConfig, Bunch)):
                key = f"__{obj.__class__.__name__}__"
                return {key: obj.__dict__}
            return json.JSONEncoder.default(self, obj)

    @staticmethod
    def CustomTypeDecoder(dct):
        if '__CloudManConfig__' in dct:
            return CloudManConfig(**dct['__CloudManConfig__'])
        elif '__Bunch__' in dct:
            return Bunch(**dct['__Bunch__'])
        else:
            return dct

    @staticmethod
    def load_config(fp):
        return json.load(fp, object_hook=CloudManConfig.CustomTypeDecoder)

    def save_config(self, fp):
        json.dump(self, fp, cls=self.CustomTypeEncoder)

    def validate(self):
        if self.access_key is None:
            return "Access key must not be null"
        elif self.secret_key is None:
            return "Secret key must not be null"
        elif self.cluster_name is None:
            return "Cluster name must not be null"
        elif self.image_id is None:
            return "Image ID must not be null"
        elif self.instance_type is None:
            return "Instance type must not be null"
        elif self.password is None:
            return "Password must not be null"
        elif self.cluster_type not in [None, 'Test', 'Data', 'Galaxy', 'Shared_cluster']:
            return f"Unrecognized cluster type ({self.cluster_type})"
        elif self.galaxy_data_option not in [None, '', 'custom-size', 'transient']:
            return f"Unrecognized galaxy data option ({self.galaxy_data_option})"
        elif self.key_name is None:
            return "Key-pair name must not be null"
        else:
            return None


class GenericVMInstance:

    def __init__(self, launcher, launch_result):
        """
        Create an instance of the CloudMan API class, which is to be used when
        manipulating that given CloudMan instance.

        The ``url`` is a string defining the address of CloudMan, for
        example "http://115.146.92.174". The ``password`` is CloudMan's password,
        as defined in the user data sent to CloudMan on instance creation.
        """
        # Make sure the url scheme is defined (otherwise requests will not work)
        self.vm_error = None
        self.vm_status = None
        self.host_name = None
        self.launcher = launcher
        self.launch_result = launch_result

    def _update_host_name(self, host_name):
        if self.host_name != host_name:
            self.host_name = host_name

    @property
    def instance_id(self):
        """
        Returns the ID of this instance (e.g., ``i-87ey32dd``) if launch was
        successful or ``None`` otherwise.
        """
        return None if self.launch_result is None else self.launch_result['instance_id']

    @property
    def key_pair_name(self):
        """
        Returns the name of the key pair used by this instance. If instance was
        not launched properly, returns ``None``.
        """
        return None if self.launch_result is None else self.launch_result['kp_name']

    @property
    def key_pair_material(self):
        """
        Returns the private portion of the generated key pair. It does so only
        if the instance was properly launched and key pair generated; ``None``
        otherwise.
        """
        return None if self.launch_result is None else self.launch_result['kp_material']

    def get_machine_status(self):
        """
        Check on the underlying VM status of an instance. This can be used to
        determine whether the VM has finished booting up and if CloudMan
        is up and running.

        Return a ``state`` dict with the current ``instance_state``, ``public_ip``,
        ``placement``, and ``error`` keys, which capture the current state (the
        values for those keys default to empty string if no data is available from
        the cloud).
        """
        if self.launcher:
            return self.launcher.get_status(self.instance_id)
        # elif self.host_name:

        else:
            state = {'instance_state': "",
                     'public_ip': "",
                     'placement': "",
                     'error': "No reference to the instance object"}
            return state

    def _init_instance(self, host_name):
        self._update_host_name(host_name)

    def wait_until_instance_ready(self, vm_ready_timeout=300, vm_ready_check_interval=10):
        """
        Wait until the VM state changes to ready/error or timeout elapses.
        Updates the host name once ready.
        """
        assert vm_ready_timeout > 0
        assert vm_ready_timeout > vm_ready_check_interval
        assert vm_ready_check_interval > 0

        if self.host_name:  # Host name available. Therefore, instance is ready
            return

        for time_left in range(vm_ready_timeout, 0, -vm_ready_check_interval):
            status = self.get_machine_status()
            if status['public_ip'] != '' and status['error'] == '':
                self._init_instance(status['public_ip'])
                return
            elif status['error'] != '':
                msg = f"Error launching an instance: {status['error']}"
                bioblend.log.error(msg)
                raise VMLaunchException(msg)
            else:
                bioblend.log.warning(
                    f"Instance not ready yet (it's in state '{status['instance_state']}'); waiting another {time_left} seconds..."
                )
                time.sleep(vm_ready_check_interval)

        raise VMLaunchException(
            f"Waited too long for instance to become ready. Instance Id: {self.instance_id}"
        )


class CloudManInstance(GenericVMInstance):

    def __init__(self, url, password, **kwargs):
        """
        Create an instance of the CloudMan API class, which is to be used when
        manipulating that given CloudMan instance.

        The ``url`` is a string defining the address of CloudMan, for
        example "http://115.146.92.174". The ``password`` is CloudMan's password,
        as defined in the user data sent to CloudMan on instance creation.
        """
        self.initialized = False
        if kwargs.get('launch_result', None) is not None:  # Used internally by the launch_instance method
            super().__init__(kwargs['launcher'], kwargs['launch_result'])
        else:
            super().__init__(None, None)
        self.config = kwargs.pop('cloudman_config', CloudManConfig())
        self.password = password or self.config.password
        self.use_ssl = kwargs.get("use_ssl", self.config.kwargs.get("use_ssl", False))
        self.verify = kwargs.get("verify", self.config.kwargs.get("verify", False))
        self.authuser = kwargs.get("authuser", "")
        self._set_url(url)

    def __repr__(self):
        if self.cloudman_url:
            return f"CloudMan instance at {self.cloudman_url}"
        else:
            return "Waiting for this CloudMan instance to start..."

    def _update_host_name(self, host_name):
        """
        Overrides the super-class method and makes sure that the ``cloudman_url``
        is kept in sync with the host name.
        """
        self._set_url(host_name)

    def _init_instance(self, hostname):
        super()._init_instance(hostname)
        if self.config.cluster_type:
            self.initialize(self.config.cluster_type, galaxy_data_option=self.config.galaxy_data_option, initial_storage_size=self.config.initial_storage_size)

    def _set_url(self, url):
        """
        Keeps the CloudMan URL as well and the hostname in sync.
        """
        if url:
            # Make sure the URL scheme is defined (otherwise requests will not work)
            if not url.lower().startswith('http'):
                # Check to see whether https scheme is required
                if self.use_ssl:
                    url = "https://" + url
                else:
                    url = "http://" + url
            # Parse the corrected URL again to extract the hostname
            parse_result = urlparse(url)
            super()._update_host_name(parse_result.hostname)
        self.url = url

    @property
    def galaxy_url(self):
        """
        Returns the base URL for this instance, which by default happens to be
        the URL for Galaxy application.
        """
        return self.url

    @property
    def cloudman_url(self):
        """
        Returns the URL for accessing this instance of CloudMan.
        """
        if self.url:
            return self.url + '/cloud'
        return None

    @staticmethod
    def launch_instance(cfg, **kwargs):
        """
        Launches a new instance of CloudMan on the specified cloud infrastructure.

        :type cfg: CloudManConfig
        :param cfg: A CloudManConfig object containing the initial parameters
                    for this launch.
        """
        validation_result = cfg.validate()
        if validation_result is not None:
            raise VMLaunchException(
                f"Invalid CloudMan configuration provided: {validation_result}"
            )
        launcher = CloudManLauncher(cfg.access_key, cfg.secret_key, cfg.cloud_metadata)
        result = launcher.launch(
            cfg.cluster_name, cfg.image_id, cfg.instance_type, cfg.password,
            cfg.kernel_id, cfg.ramdisk_id, cfg.key_name, cfg.security_groups,
            cfg.placement, **cfg.kwargs)
        if result['error'] is not None:
            raise VMLaunchException(f"Error launching cloudman instance: {result['error']}")
        instance = CloudManInstance(None, None, launcher=launcher,
                                    launch_result=result, cloudman_config=cfg)
        if cfg.block_until_ready and cfg.cluster_type:
            instance.get_status()  # this will indirect result in initialize being invoked
        return instance

    def update(self):
        """
        Update the local object's fields to be in sync with the actual state
        of the CloudMan instance the object points to. This method should be
        called periodically to ensure you are looking at the current data.

        .. versionadded:: 0.2.2
        """
        ms = self.get_machine_status()
        # Check if the machine is running and update IP and state
        self.vm_status = ms.get('instance_state', None)
        self.vm_error = ms.get('error', None)
        public_ip = ms.get('public_ip', None)
        # Update url if we don't have it or is different than what we have
        if not self.url and (public_ip and self.url != public_ip):
            self._set_url(public_ip)
        # See if the cluster has been initialized
        if self.vm_status == 'running' or self.url:
            ct = self.get_cluster_type()
            if ct.get('cluster_type', None):
                self.initialized = True
        if self.vm_error:
            bioblend.log.error(self.vm_error)

    @block_until_vm_ready
    def get_cloudman_version(self):
        """
        Returns the cloudman version from the server. Versions prior to Cloudman 2 does not
        support this call, and therefore, the default is to return 1
        """
        try:
            r = self._make_get_request("cloudman_version")
            return r['version']
        except Exception:
            return 1

    @block_until_vm_ready
    def initialize(self, cluster_type, galaxy_data_option='', initial_storage_size=None, shared_bucket=None):
        """
        Initialize CloudMan platform. This needs to be done before the cluster
        can be used.

        The ``cluster_type``, either 'Galaxy', 'Data', or 'Test', defines the type
        of cluster platform to initialize.
        """
        if not self.initialized:
            if self.get_cloudman_version() < 2:
                r = self._make_get_request(
                    "initialize_cluster",
                    parameters={
                        'startup_opt': cluster_type,
                        'g_pss': initial_storage_size,
                        'shared_bucket': shared_bucket
                    })
            else:
                r = self._make_get_request(
                    "initialize_cluster",
                    parameters={
                        'startup_opt': cluster_type,
                        'galaxy_data_option': galaxy_data_option,
                        'pss': initial_storage_size,
                        'shared_bucket': shared_bucket
                    })
            self.initialized = True
            return r

    @block_until_vm_ready
    def get_cluster_type(self):
        """
        Get the ``cluster type`` for this CloudMan instance. See the
        CloudMan docs about the available types. Returns a dictionary,
        for example: ``{'cluster_type': 'Test'}``.
        """
        cluster_type = self._make_get_request("cluster_type")
        if cluster_type['cluster_type']:
            self.initialized = True
        return cluster_type

    @block_until_vm_ready
    def get_status(self):
        """
        Get status information on this CloudMan instance.
        """
        return self._make_get_request("instance_state_json")

    @block_until_vm_ready
    def get_nodes(self):
        """
        Get a list of nodes currently running in this CloudMan cluster.
        """
        instance_feed_json = self._make_get_request("instance_feed_json")
        return instance_feed_json['instances']

    @block_until_vm_ready
    def get_cluster_size(self):
        """
        Get the size of the cluster in terms of the number of nodes; this count
        includes the master node.
        """
        return len(self.get_nodes())

    @block_until_vm_ready
    def get_static_state(self):
        """
        Get static information on this CloudMan instance.
        i.e. state that doesn't change over the lifetime of the cluster
        """
        return self._make_get_request("static_instance_state_json")

    @block_until_vm_ready
    def get_master_ip(self):
        """
        Returns the public IP of the master node in this CloudMan cluster
        """
        status_json = self.get_static_state()
        return status_json['master_ip']

    @block_until_vm_ready
    def get_master_id(self):
        """
        Returns the instance ID of the master node in this CloudMan cluster
        """
        status_json = self.get_static_state()
        return status_json['master_id']

    @block_until_vm_ready
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
        return self._make_get_request("add_instances", parameters=payload)

    @block_until_vm_ready
    def remove_nodes(self, num_nodes, force=False):
        """
        Remove worker nodes from the cluster.

        The ``num_nodes`` parameter defines the number of worker nodes to remove.
        The ``force`` parameter (defaulting to False), is a boolean indicating
        whether the nodes should be forcibly removed rather than gracefully removed.
        """
        payload = {'number_nodes': num_nodes, 'force_termination': force}
        result = self._make_get_request("remove_instances", parameters=payload)
        return result

    @block_until_vm_ready
    def remove_node(self, instance_id, force=False):
        """
        Remove a specific worker node from the cluster.

        The ``instance_id`` parameter defines the ID, as a string, of a worker node
        to remove from the cluster. The ``force`` parameter (defaulting to False),
        is a boolean indicating whether the node should be forcibly removed rather
        than gracefully removed.

        """
        payload = {'instance_id': instance_id}
        return self._make_get_request("remove_instance", parameters=payload)

    @block_until_vm_ready
    def reboot_node(self, instance_id):
        """
        Reboot a specific worker node.

        The ``instance_id`` parameter defines the ID, as a string, of a worker node
        to reboot.
        """
        payload = {'instance_id': instance_id}
        return self._make_get_request("reboot_instance", parameters=payload)

    @block_until_vm_ready
    def autoscaling_enabled(self):
        """
        Returns a boolean indicating whether autoscaling is enabled.
        """
        return bool(self.get_status()['autoscaling']['use_autoscaling'])

    @block_until_vm_ready
    def enable_autoscaling(self, minimum_nodes=0, maximum_nodes=19):
        """
        Enable cluster autoscaling, allowing the cluster to automatically add,
        or remove, worker nodes, as needed.

        The number of worker nodes in the cluster is bounded by the ``minimum_nodes``
        (default is 0) and ``maximum_nodes`` (default is 19) parameters.
        """
        if not self.autoscaling_enabled():
            payload = {'as_min': minimum_nodes, 'as_max': maximum_nodes}
            self._make_get_request("toggle_autoscaling", parameters=payload)

    @block_until_vm_ready
    def disable_autoscaling(self):
        """
        Disable autoscaling, meaning that worker nodes will need to be manually
        added and removed.
        """
        if self.autoscaling_enabled():
            self._make_get_request("toggle_autoscaling")

    @block_until_vm_ready
    def adjust_autoscaling(self, minimum_nodes=None, maximum_nodes=None):
        """
        Adjust the autoscaling configuration parameters.

        The number of worker nodes in the cluster is bounded by the optional
        ``minimum_nodes`` and ``maximum_nodes`` parameters. If a parameter is
        not provided then its configuration value does not change.
        """
        if self.autoscaling_enabled():
            payload = {'as_min_adj': minimum_nodes, 'as_max_adj': maximum_nodes}
            self._make_get_request("adjust_autoscaling", parameters=payload)

    @block_until_vm_ready
    def is_master_execution_host(self):
        """
        Checks whether the master node has job execution enabled.

        """
        status = self._make_get_request("get_all_services_status")
        return bool(status['master_is_exec_host'])

    @block_until_vm_ready
    def set_master_as_execution_host(self, enable):
        """
        Enables/disables master as execution host.

        """
        if not self.is_master_execution_host():
            self._make_get_request("toggle_master_as_exec_host")

    @block_until_vm_ready
    def get_galaxy_state(self):
        """
        Get the current status of Galaxy running on the cluster.
        """
        payload = {'srvc': 'Galaxy'}
        status = self._make_get_request("get_srvc_status", parameters=payload)
        return {'status': status['status']}

    @block_until_vm_ready
    def terminate(self, terminate_master_instance=True, delete_cluster=False):
        """
        Terminate this CloudMan cluster. There is an option to also terminate the
        master instance (all worker instances will be terminated in the process
        of cluster termination), and delete the whole cluster.

        .. warning::
            Deleting a cluster is irreversible - all of the data will be
            permanently deleted.
        """
        payload = {'terminate_master_instance': terminate_master_instance,
                   'delete_cluster': delete_cluster}
        result = self._make_get_request("kill_all", parameters=payload,
                                        timeout=15)
        return result

    def _make_get_request(self, url, parameters=None, timeout=None):
        """
        Private function that makes a GET request to the nominated ``url``,
        with the provided GET ``parameters``. Optionally, set the ``timeout``
        to stop waiting for a response after a given number of seconds. This is
        particularly useful when terminating a cluster as it may terminate
        before sending a response.
        """
        if parameters is None:
            parameters = {}
        req_url = '/'.join((self.cloudman_url, 'root', url))
        r = requests.get(
            req_url,
            params=parameters,
            auth=(self.authuser, self.password),
            timeout=timeout,
            verify=self.verify,
        )
        try:
            json = r.json()
            return json
        except Exception:
            return r.text
