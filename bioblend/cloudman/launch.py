"""
Setup and launch a CloudMan instance.
"""
import datetime
import socket
from http.client import (
    BadStatusLine,
    HTTPConnection,
    HTTPException,
)
from urllib.parse import urlparse

import boto
import yaml
from boto.ec2.regioninfo import RegionInfo
from boto.exception import EC2ResponseError, S3ResponseError
from boto.s3.connection import OrdinaryCallingFormat, S3Connection, SubdomainCallingFormat

import bioblend
from bioblend.util import Bunch


# Uncomment the following line if no logging from boto is desired
# bioblend.logging.getLogger('boto').setLevel(bioblend.logging.CRITICAL)
# Uncomment the following line if logging at the prompt is desired
# bioblend.set_stream_logger(__name__)
def instance_types(cloud_name='generic'):
    """
    Return a list of dictionaries containing details about the available
    instance types for the given `cloud_name`.

    :type cloud_name: str
    :param cloud_name: A name of the cloud for which the list of instance
                       types will be returned. Valid values are: `aws`,
                       `nectar`, `generic`.

    :rtype: list
    :return: A list of dictionaries describing instance types. Each dict will
             contain the following keys: `name`, `model`, and `description`.
    """
    instance_list = []
    if cloud_name.lower() == 'aws':
        instance_list.append({"model": "c3.large",
                              "name": "Compute optimized Large",
                              "description": "2 vCPU/4GB RAM"})
        instance_list.append({"model": "c3.2xlarge",
                              "name": "Compute optimized 2xLarge",
                              "description": "8 vCPU/15GB RAM"})
        instance_list.append({"model": "c3.8xlarge",
                              "name": "Compute optimized 8xLarge",
                              "description": "32 vCPU/60GB RAM"})
    elif cloud_name.lower() in ['nectar', 'generic']:
        instance_list.append({"model": "m1.small",
                              "name": "Small",
                              "description": "1 vCPU / 4GB RAM"})
        instance_list.append({"model": "m1.medium",
                              "name": "Medium",
                              "description": "2 vCPU / 8GB RAM"})
        instance_list.append({"model": "m1.large",
                              "name": "Large",
                              "description": "4 vCPU / 16GB RAM"})
        instance_list.append({"model": "m1.xlarge",
                              "name": "Extra Large",
                              "description": "8 vCPU / 32GB RAM"})
        instance_list.append({"model": "m1.xxlarge",
                              "name": "Extra-extra Large",
                              "description": "16 vCPU / 64GB RAM"})
    return instance_list


class CloudManLauncher:

    def __init__(self, access_key, secret_key, cloud=None):
        """
        Define the environment in which this instance of CloudMan will be launched.

        Besides providing the credentials, optionally provide the ``cloud``
        object. This object must define the properties required to establish a
        `boto <https://github.com/boto/boto/>`_ connection to that cloud. See
        this method's implementation for an example of the required fields.
        Note that as long the as provided object defines the required fields,
        it can really by implemented as anything (e.g., a Bunch, a database
        object, a custom class). If no value for the ``cloud`` argument is
        provided, the default is to use the Amazon cloud.
        """
        self.access_key = access_key
        self.secret_key = secret_key
        if cloud is None:
            # Default to an EC2-compatible object
            self.cloud = Bunch(id='1',  # for compatibility w/ DB representation
                               name="Amazon",
                               cloud_type="ec2",
                               bucket_default="cloudman",
                               region_name="us-east-1",
                               region_endpoint="ec2.amazonaws.com",
                               ec2_port="",
                               ec2_conn_path="/",
                               cidr_range="",
                               is_secure=True,
                               s3_host="s3.amazonaws.com",
                               s3_port="",
                               s3_conn_path='/')
        else:
            self.cloud = cloud
        self.ec2_conn = self.connect_ec2(
            self.access_key,
            self.secret_key,
            self.cloud)
        self.vpc_conn = self.connect_vpc(
            self.access_key,
            self.secret_key,
            self.cloud)
        # Define exceptions that we want to catch and retry
        self.http_exceptions = (
            HTTPException,
            socket.error,
            socket.gaierror,
            BadStatusLine
        )

    def __repr__(self):
        return f"Cloud: {self.cloud.name}; acct ID: {self.access_key}"

    def launch(self, cluster_name, image_id, instance_type, password,
               kernel_id=None, ramdisk_id=None, key_name='cloudman_key_pair',
               security_groups=None, placement='', subnet_id=None,
               ebs_optimized=False, **kwargs):
        """
        Check all the prerequisites (key pair and security groups) for
        launching a CloudMan instance, compose the user data based on the
        parameters specified in the arguments and the cloud properties as
        defined in the object's ``cloud`` field.

        For the current list of user data fields that can be provided via
        ``kwargs``, see `<https://galaxyproject.org/cloudman/userdata/>`_

        Return a dict containing the properties and info with which an instance
        was launched, namely: ``sg_names`` containing the names of the security
        groups, ``kp_name`` containing the name of the key pair, ``kp_material``
        containing the private portion of the key pair (*note* that this portion
        of the key is available and can be retrieved *only* at the time the key
        is created, which will happen only if no key with the name provided in
        the ``key_name`` argument exists), ``rs`` containing the
        `boto <https://github.com/boto/boto/>`_ ``ResultSet`` object,
        ``instance_id`` containing the ID of a started instance, and
        ``error`` containing an error message if there was one.
        """
        if security_groups is None:
            security_groups = ['CloudMan']
        ret = {'sg_names': [],
               'sg_ids': [],
               'kp_name': '',
               'kp_material': '',
               'rs': None,
               'instance_id': '',
               'error': None}
        # First satisfy the prerequisites
        for sg in security_groups:
            # Get VPC ID in case we're launching into a VPC
            vpc_id = None
            if subnet_id:
                try:
                    sn = self.vpc_conn.get_all_subnets(subnet_id)[0]
                    vpc_id = sn.vpc_id
                except (EC2ResponseError, IndexError):
                    bioblend.log.exception("Trouble fetching subnet %s", subnet_id)
            cmsg = self.create_cm_security_group(sg, vpc_id=vpc_id)
            ret['error'] = cmsg['error']
            if ret['error']:
                return ret
            if cmsg['name']:
                ret['sg_names'].append(cmsg['name'])
                ret['sg_ids'].append(cmsg['sg_id'])
                if subnet_id:
                    # Must setup a network interface if launching into VPC
                    security_groups = None
                    interface = boto.ec2.networkinterface.NetworkInterfaceSpecification(
                        subnet_id=subnet_id, groups=[cmsg['sg_id']],
                        associate_public_ip_address=True)
                    network_interfaces = (boto.ec2.networkinterface.
                                          NetworkInterfaceCollection(interface))
                else:
                    network_interfaces = None
        kp_info = self.create_key_pair(key_name)
        ret['kp_name'] = kp_info['name']
        ret['kp_material'] = kp_info['material']
        ret['error'] = kp_info['error']
        if ret['error']:
            return ret
        # If not provided, try to find a placement
        # TODO: Should placement always be checked? To make sure it's correct
        # for existing clusters.
        if not placement:
            placement = self._find_placement(
                cluster_name).get('placement', None)
        # Compose user data for launching an instance, ensuring we have the
        # required fields
        kwargs['access_key'] = self.access_key
        kwargs['secret_key'] = self.secret_key
        kwargs['cluster_name'] = cluster_name
        kwargs['password'] = password
        kwargs['cloud_name'] = self.cloud.name
        ud = self._compose_user_data(kwargs)
        # Now launch an instance
        try:

            rs = None
            rs = self.ec2_conn.run_instances(image_id=image_id,
                                             instance_type=instance_type,
                                             key_name=key_name,
                                             security_groups=security_groups,
                                             # The following two arguments are
                                             # provided in the network_interface
                                             # instead of arguments:
                                             # security_group_ids=security_group_ids,
                                             # subnet_id=subnet_id,
                                             network_interfaces=network_interfaces,
                                             user_data=ud,
                                             kernel_id=kernel_id,
                                             ramdisk_id=ramdisk_id,
                                             placement=placement,
                                             ebs_optimized=ebs_optimized)
            ret['rs'] = rs
        except EC2ResponseError as e:
            err_msg = f"Problem launching an instance: {e} (code {e.error_code}; status {e.status})"
            bioblend.log.exception(err_msg)
            ret['error'] = err_msg
            return ret
        else:
            if rs:
                try:
                    bioblend.log.info("Launched an instance with ID %s", rs.instances[0].id)
                    ret['instance_id'] = rs.instances[0].id
                    ret['instance_ip'] = rs.instances[0].ip_address
                except EC2ResponseError as e:
                    err_msg = f"Problem with the launched instance object: {e} (code {e.error_code}; status {e.status})"
                    bioblend.log.exception(err_msg)
                    ret['error'] = err_msg
            else:
                ret['error'] = ("No response after launching an instance. Check "
                                "your account permissions and try again.")
        return ret

    def create_cm_security_group(self, sg_name='CloudMan', vpc_id=None):
        """
        Create a security group with all authorizations required to run CloudMan.

        If the group already exists, check its rules and add the missing ones.

        :type sg_name: str
        :param sg_name: A name for the security group to be created.

        :type vpc_id: str
        :param vpc_id: VPC ID under which to create the security group.

        :rtype: dict
        :return: A dictionary containing keys ``name`` (with the value being the
                 name of the security group that was created), ``error``
                 (with the value being the error message if there was an error
                 or ``None`` if no error was encountered), and ``ports``
                 (containing the list of tuples with port ranges that were
                 opened or attempted to be opened).

        .. versionchanged:: 0.6.1
            The return value changed from a string to a dict
        """
        ports = (('20', '21'),  # FTP
                 ('22', '22'),  # SSH
                 ('80', '80'),  # Web UI
                 ('443', '443'),  # SSL Web UI
                 ('8800', '8800'),  # NodeJS Proxy for Galaxy IPython IE
                 ('9600', '9700'),  # HTCondor
                 ('30000', '30100'))  # FTP transfer
        progress = {'name': None,
                    'sg_id': None,
                    'error': None,
                    'ports': ports}
        cmsg = None
        filters = None
        if vpc_id:
            filters = {'vpc-id': vpc_id}
        # Check if this security group already exists
        try:
            sgs = self.ec2_conn.get_all_security_groups(filters=filters)
        except EC2ResponseError as e:
            err_msg = f"Problem getting security groups. This could indicate a problem with your account credentials or permissions: {e} (code {e.error_code}; status {e.status})"
            bioblend.log.exception(err_msg)
            progress['error'] = err_msg
            return progress
        for sg in sgs:
            if sg.name == sg_name:
                cmsg = sg
                bioblend.log.debug("Security group '%s' already exists; will add authorizations next.", sg_name)
                break
        # If it does not exist, create security group
        if cmsg is None:
            bioblend.log.debug("Creating Security Group %s", sg_name)
            try:
                cmsg = self.ec2_conn.create_security_group(sg_name, 'A security '
                                                           'group for CloudMan',
                                                           vpc_id=vpc_id)
            except EC2ResponseError as e:
                err_msg = f"Problem creating security group '{sg_name}': {e} (code {e.error_code}; status {e.status})"
                bioblend.log.exception(err_msg)
                progress['error'] = err_msg
        if cmsg:
            progress['name'] = cmsg.name
            progress['sg_id'] = cmsg.id
            # Add appropriate authorization rules
            # If these rules already exist, nothing will be changed in the SG
            for port in ports:
                try:
                    if not self.rule_exists(
                            cmsg.rules, from_port=port[0], to_port=port[1]):
                        cmsg.authorize(
                            ip_protocol='tcp',
                            from_port=port[0],
                            to_port=port[1],
                            cidr_ip='0.0.0.0/0')
                    else:
                        bioblend.log.debug("Rule (%s:%s) already exists in the SG", port[0], port[1])
                except EC2ResponseError as e:
                    err_msg = f"A problem adding security group authorizations: {e} (code {e.error_code}; status {e.status})"
                    bioblend.log.exception(err_msg)
                    progress['error'] = err_msg
            # Add ICMP (i.e., ping) rule required by HTCondor
            try:
                if not self.rule_exists(
                        cmsg.rules, from_port='-1', to_port='-1', ip_protocol='icmp'):
                    cmsg.authorize(
                        ip_protocol='icmp',
                        from_port=-1,
                        to_port=-1,
                        cidr_ip='0.0.0.0/0')
                else:
                    bioblend.log.debug(
                        f"ICMP rule already exists in {sg_name} SG.")
            except EC2ResponseError as e:
                err_msg = f"A problem with security ICMP rule authorization: {e} (code {e.error_code}; status {e.status})"
                bioblend.log.exception(err_msg)
                progress['err_msg'] = err_msg
            # Add rule that allows communication between instances in the same
            # SG
            # A flag to indicate if group rule already exists
            g_rule_exists = False
            for rule in cmsg.rules:
                for grant in rule.grants:
                    if grant.name == cmsg.name:
                        g_rule_exists = True
                        bioblend.log.debug(
                            "Group rule already exists in the SG.")
                if g_rule_exists:
                    break
            if not g_rule_exists:
                try:
                    cmsg.authorize(
                        src_group=cmsg,
                        ip_protocol='tcp',
                        from_port=0,
                        to_port=65535)
                except EC2ResponseError as e:
                    err_msg = f"A problem with security group group authorization: {e} (code {e.error_code}; status {e.status})"
                    bioblend.log.exception(err_msg)
                    progress['err_msg'] = err_msg
            bioblend.log.info("Done configuring '%s' security group", cmsg.name)
        else:
            bioblend.log.warning(
                f"Did not create security group '{sg_name}'")
        return progress

    def rule_exists(
            self, rules, from_port, to_port, ip_protocol='tcp', cidr_ip='0.0.0.0/0'):
        """
        A convenience method to check if an authorization rule in a security group
        already exists.
        """
        for rule in rules:
            if rule.ip_protocol == ip_protocol and rule.from_port == from_port and \
               rule.to_port == to_port and cidr_ip in [ip.cidr_ip for ip in rule.grants]:
                return True
        return False

    def create_key_pair(self, key_name='cloudman_key_pair'):
        """
        If a key pair with the provided ``key_name`` does not exist, create it.

        :type sg_name: str
        :param sg_name: A name for the key pair to be created.

        :rtype: dict
        :return: A dictionary containing keys ``name`` (with the value being the
                 name of the key pair that was created), ``error``
                 (with the value being the error message if there was an error
                 or ``None`` if no error was encountered), and ``material``
                 (containing the unencrypted PEM encoded RSA private key if the
                 key was created or ``None`` if the key already eixsted).

        .. versionchanged:: 0.6.1
            The return value changed from a tuple to a dict
        """
        progress = {'name': None,
                    'material': None,
                    'error': None}
        kp = None
        # Check if a key pair under the given name already exists. If it does not,
        # create it, else return.
        try:
            kps = self.ec2_conn.get_all_key_pairs()
        except EC2ResponseError as e:
            err_msg = f"Problem getting key pairs: {e} (code {e.error_code}; status {e.status})"
            bioblend.log.exception(err_msg)
            progress['error'] = err_msg
            return progress
        for akp in kps:
            if akp.name == key_name:
                bioblend.log.info("Key pair '%s' already exists; reusing it.", key_name)
                progress['name'] = akp.name
                return progress
        try:
            kp = self.ec2_conn.create_key_pair(key_name)
        except EC2ResponseError as e:
            err_msg = f"Problem creating key pair '{key_name}': {e} (code {e.error_code}; status {e.status})"
            bioblend.log.exception(err_msg)
            progress['error'] = err_msg
            return progress
        bioblend.log.info("Created key pair '%s'", kp.name)
        progress['name'] = kp.name
        progress['material'] = kp.material
        return progress

    def assign_floating_ip(self, ec2_conn, instance):
        try:
            bioblend.log.debug("Allocating a new floating IP address.")
            address = ec2_conn.allocate_address()
        except EC2ResponseError:
            bioblend.log.exception("Exception allocating a new floating IP address")
        bioblend.log.info("Associating floating IP %s to instance %s", address.public_ip, instance.id)
        ec2_conn.associate_address(instance_id=instance.id,
                                   public_ip=address.public_ip)

    def get_status(self, instance_id):
        """
        Check on the status of an instance. ``instance_id`` needs to be a
        ``boto``-library copatible instance ID (e.g., ``i-8fehrdss``).If
        ``instance_id`` is not provided, the ID obtained when launching
        *the most recent* instance is used. Note that this assumes the instance
        being checked on was launched using this  class. Also note that the same
        class may be used to launch multiple instances but only the most recent
        ``instance_id`` is kept while any others will  to be explicitly specified.

        This method also allows the required ``ec2_conn`` connection object to be
        provided at invocation time. If the object is not provided, credentials
        defined for the class are used (ability to specify a custom ``ec2_conn``
        helps in case of stateless method invocations).

        Return a ``state`` dict containing the following keys: ``instance_state``,
        ``public_ip``, ``placement``, and ``error``, which capture CloudMan's
        current state. For ``instance_state``, expected values are: ``pending``,
        ``booting``, ``running``, or ``error`` and represent the state of the
        underlying instance. Other keys will return an empty  value until the
        ``instance_state`` enters ``running`` state.
        """
        ec2_conn = self.ec2_conn
        rs = None
        state = {'instance_state': "",
                 'public_ip': "",
                 'placement': "",
                 'error': ""}

        # Make sure we have an instance ID
        if instance_id is None:
            err = "Missing instance ID, cannot check the state."
            bioblend.log.error(err)
            state['error'] = err
            return state
        try:
            rs = ec2_conn.get_all_instances([instance_id])
            if rs is not None:
                inst_state = rs[0].instances[0].update()
                public_ip = rs[0].instances[0].ip_address
                state['public_ip'] = public_ip
                if inst_state == 'running':
                    # if there's a private ip, but no public ip
                    # attempt auto allocation of floating IP
                    if rs[0].instances[0].private_ip_address and not public_ip:
                        self.assign_floating_ip(ec2_conn, rs[0].instances[0])
                    # Wait until the CloudMan URL is accessible to return
                    # the data - this may only be correct initially at
                    # bootup for instances that configure themselves for
                    # https - they may ultimately block port 80. However,
                    # we don't have a good way to determine whether to
                    # check using http or https.
                    cm_url = f"http://{public_ip}/cloud"
                    if self._checkURL(cm_url) is True:
                        state['instance_state'] = inst_state
                        state['placement'] = rs[0].instances[0].placement
                    else:
                        state['instance_state'] = 'booting'
                else:
                    state['instance_state'] = inst_state
        except Exception as e:
            err = f"Problem updating instance '{instance_id}' state: {e}"
            bioblend.log.error(err)
            state['error'] = err
        return state

    def get_clusters_pd(self, include_placement=True):
        """
        Return *persistent data* of all existing clusters for this account.

        :type include_placement: bool
        :param include_placement: Whether or not to include region placement for
                                  the clusters. Setting this option will lead
                                  to a longer function runtime.

        :rtype: dict
        :return: A dictionary containing keys ``clusters`` and ``error``. The
                 value of ``clusters`` will be a dictionary with the following keys
                 ``cluster_name``, ``persistent_data``, ``bucket_name`` and optionally
                 ``placement`` or an empty list if no clusters were found or an
                 error was encountered. ``persistent_data`` key value is yet
                 another dictionary containing given cluster's persistent data.
                 The value for the ``error`` key will contain a string with the
                 error message.

        .. versionadded:: 0.3
        .. versionchanged:: 0.7.0
            The return value changed from a list to a dictionary.
        """
        clusters = []
        response = {'clusters': clusters, 'error': None}
        s3_conn = self.connect_s3(self.access_key, self.secret_key, self.cloud)
        try:
            buckets = s3_conn.get_all_buckets()
        except S3ResponseError as e:
            response['error'] = f"S3ResponseError getting buckets: {e}"
        except self.http_exceptions as ex:
            response['error'] = f"Exception getting buckets: {ex}"
        if response['error']:
            bioblend.log.exception(response['error'])
            return response
        for bucket in [b for b in buckets if b.name.startswith('cm-')]:
            try:
                # TODO: first lookup if persistent_data.yaml key exists
                pd = bucket.get_key('persistent_data.yaml')
            except S3ResponseError:
                # This can fail for a number of reasons for non-us and/or
                # CNAME'd buckets but it is not a terminal error
                bioblend.log.warning("Problem fetching persistent_data.yaml from bucket %s", bucket)
                continue
            if pd:
                # We are dealing with a CloudMan bucket
                pd_contents = pd.get_contents_as_string()
                pd = yaml.load(pd_contents)
                if 'cluster_name' in pd:
                    cluster_name = pd['cluster_name']
                else:
                    for key in bucket.list():
                        if key.name.endswith('.clusterName'):
                            cluster_name = key.name.split('.clusterName')[0]
                cluster = {'cluster_name': cluster_name,
                           'persistent_data': pd,
                           'bucket_name': bucket.name}
                # Look for cluster's placement too
                if include_placement:
                    placement = self._find_placement(cluster_name, cluster)
                    cluster['placement'] = placement
                clusters.append(cluster)
        response['clusters'] = clusters
        return response

    def get_cluster_pd(self, cluster_name):
        """
        Return *persistent data* (as a dict) associated with a cluster with the
        given ``cluster_name``. If a cluster with the given name is not found,
        return an empty dict.

        .. versionadded:: 0.3
        """
        cluster = {}
        clusters = self.get_clusters_pd().get('clusters', [])
        for c in clusters:
            if c['cluster_name'] == cluster_name:
                cluster = c
                break
        return cluster

    def connect_ec2(self, a_key, s_key, cloud=None):
        """
        Create and return an EC2-compatible connection object for the given cloud.

        See ``_get_cloud_info`` method for more details on the requirements for
        the ``cloud`` parameter. If no value is provided, the class field is used.
        """
        if cloud is None:
            cloud = self.cloud
        ci = self._get_cloud_info(cloud)
        r = RegionInfo(name=ci['region_name'], endpoint=ci['region_endpoint'])
        ec2_conn = boto.connect_ec2(aws_access_key_id=a_key,
                                    aws_secret_access_key=s_key,
                                    is_secure=ci['is_secure'],
                                    region=r,
                                    port=ci['ec2_port'],
                                    path=ci['ec2_conn_path'],
                                    validate_certs=False)
        return ec2_conn

    def connect_s3(self, a_key, s_key, cloud=None):
        """
        Create and return an S3-compatible connection object for the given cloud.

        See ``_get_cloud_info`` method for more details on the requirements for
        the ``cloud`` parameter. If no value is provided, the class field is used.
        """
        if cloud is None:
            cloud = self.cloud
        ci = self._get_cloud_info(cloud)
        if ci['cloud_type'] == 'amazon':
            calling_format = SubdomainCallingFormat()
        else:
            calling_format = OrdinaryCallingFormat()
        s3_conn = S3Connection(
            aws_access_key_id=a_key, aws_secret_access_key=s_key,
            is_secure=ci['is_secure'], port=ci['s3_port'], host=ci['s3_host'],
            path=ci['s3_conn_path'], calling_format=calling_format)
        return s3_conn

    def connect_vpc(self, a_key, s_key, cloud=None):
        """
        Establish a connection to the VPC service.

        TODO: Make this work with non-default clouds as well.
        """
        if cloud is None:
            cloud = self.cloud
        ci = self._get_cloud_info(cloud)
        r = RegionInfo(name=ci['region_name'], endpoint=ci['region_endpoint'])
        vpc_conn = boto.connect_vpc(
            aws_access_key_id=a_key,
            aws_secret_access_key=s_key,
            is_secure=ci['is_secure'],
            region=r,
            port=ci['ec2_port'],
            path=ci['ec2_conn_path'],
            validate_certs=False)
        return vpc_conn

    def _compose_user_data(self, user_provided_data):
        """
        A convenience method used to compose and properly format the user data
        required when requesting an instance.

        ``user_provided_data`` is the data provided by a user required to identify
        a cluster and user other user requirements.
        """
        form_data = {}
        # Do not include the following fields in the user data but do include
        # any 'advanced startup fields' that might be added in the future
        excluded_fields = ['sg_name', 'image_id', 'instance_id', 'kp_name',
                           'cloud', 'cloud_type', 'public_dns', 'cidr_range',
                           'kp_material', 'placement', 'flavor_id']
        for key, value in user_provided_data.items():
            if key not in excluded_fields:
                form_data[key] = value
        # If the following user data keys are empty, do not include them in the
        # request user data
        udkeys = [
            'post_start_script_url',
            'worker_post_start_script_url',
            'bucket_default',
            'share_string']
        for udkey in udkeys:
            if udkey in form_data and form_data[udkey] == '':
                del form_data[udkey]
        # If bucket_default was not provided, add a default value to the user data
        # (missing value does not play nicely with CloudMan's ec2autorun.py)
        if not form_data.get(
                'bucket_default', None) and self.cloud.bucket_default:
            form_data['bucket_default'] = self.cloud.bucket_default
        # Reuse the ``password`` for the ``freenxpass`` user data option
        if 'freenxpass' not in form_data and 'password' in form_data:
            form_data['freenxpass'] = form_data['password']
        # Convert form_data into the YAML format
        ud = yaml.dump(form_data, default_flow_style=False, allow_unicode=False)
        # Also include connection info about the selected cloud
        ci = self._get_cloud_info(self.cloud, as_str=True)
        return ud + "\n" + ci

    def _get_cloud_info(self, cloud, as_str=False):
        """
        Get connection information about a given cloud
        """
        ci = {}
        ci['cloud_type'] = cloud.cloud_type
        ci['region_name'] = cloud.region_name
        ci['region_endpoint'] = cloud.region_endpoint
        ci['is_secure'] = cloud.is_secure
        ci['ec2_port'] = cloud.ec2_port if cloud.ec2_port != '' else None
        ci['ec2_conn_path'] = cloud.ec2_conn_path
        # Include cidr_range only if not empty
        if cloud.cidr_range != '':
            ci['cidr_range'] = cloud.cidr_range
        ci['s3_host'] = cloud.s3_host
        ci['s3_port'] = cloud.s3_port if cloud.s3_port != '' else None
        ci['s3_conn_path'] = cloud.s3_conn_path
        if as_str:
            ci = yaml.dump(ci, default_flow_style=False, allow_unicode=False)
        return ci

    def _get_volume_placement(self, vol_id):
        """
        Returns the placement of a volume (or None, if it cannot be determined)
        """
        try:
            vol = self.ec2_conn.get_all_volumes(volume_ids=[vol_id])
        except EC2ResponseError as ec2e:
            bioblend.log.error(f"EC2ResponseError querying for volume {vol_id}: {ec2e}")
            vol = None
        if vol:
            return vol[0].zone
        else:
            bioblend.log.error("Requested placement of a volume '%s' that does not exist.", vol_id)
            return None

    def _find_placement(self, cluster_name, cluster=None):
        """
        Find a placement zone for a cluster with the name ``cluster_name``.

        By default, this method will search for and fetch given cluster's
        *persistent data*; alternatively, *persistent data* can be provided via
        the ``cluster`` parameter. This dict needs to have ``persistent_data``
        key with the contents of cluster's *persistent data*.
        If the cluster or the volume associated with the cluster cannot be found,
        cluster placement is set to ``None``.

        :rtype: dict
        :return: A dictionary with ``placement`` and ``error`` keywords.

        .. versionchanged:: 0.7.0
            The return value changed from a list to a dictionary.
        """
        placement = None
        response = {'placement': placement, 'error': None}
        cluster = cluster or self.get_cluster_pd(cluster_name)
        if cluster and 'persistent_data' in cluster:
            pd = cluster['persistent_data']
            try:
                if 'placement' in pd:
                    response['placement'] = pd['placement']
                elif 'data_filesystems' in pd:
                    # We have v1 format persistent data so get the volume first and
                    # then the placement zone
                    vol_id = pd['data_filesystems']['galaxyData'][0]['vol_id']
                    response['placement'] = self._get_volume_placement(vol_id)
                elif 'filesystems' in pd:
                    # V2 format.
                    for fs in [fs for fs in pd['filesystems'] if fs.get(
                            'kind', None) == 'volume' and 'ids' in fs]:
                        # All volumes must be in the same zone
                        vol_id = fs['ids'][0]
                        response['placement'] = self._get_volume_placement(
                            vol_id)
                        # No need to continue to iterate through
                        # filesystems, if we found one with a volume.
                        break
            except Exception as exc:
                response['error'] = \
                    f"Exception while finding placement for cluster '{cluster_name}'. This can indicate malformed instance data. Or that this method is broken: {exc}"
                bioblend.log.error(response['error'])
                response['placement'] = None
        else:
            bioblend.log.debug(
                f"Insufficient info about cluster {cluster_name} to get placement."
            )
        return response

    def find_placements(
            self, ec2_conn, instance_type, cloud_type, cluster_name=None):
        """
        Find a list of placement zones that support the specified instance type.

        If ``cluster_name`` is given and a cluster with the given name exist,
        return a list with only one entry where the given cluster lives.

        Searching for available zones for a given instance type is done by
        checking the spot prices in the potential availability zones for
        support before deciding on a region:
        http://blog.piefox.com/2011/07/ec2-availability-zones-and-instance.html

        Note that, currently, instance-type based zone selection applies only to
        AWS. For other clouds, all the available zones are returned (unless a
        cluster is being recreated, in which case the cluster's placement zone is
        returned sa stored in its persistent data.

        :rtype: dict
        :return: A dictionary with ``zones`` and ``error`` keywords.

        .. versionchanged:: 0.3
            Changed method name from ``_find_placements`` to ``find_placements``.
            Also added ``cluster_name`` parameter.

        .. versionchanged:: 0.7.0
            The return value changed from a list to a dictionary.
        """
        # First look for a specific zone a given cluster is bound to
        zones = []
        response = {'zones': zones, 'error': None}
        if cluster_name:
            placement = self._find_placement(cluster_name)
            if placement.get('error'):
                response['error'] = placement['error']
                return response
            response['zones'] = placement.get('placement', [])
        # If placement is not found, look for a list of available zones
        if not response['zones']:
            in_the_past = datetime.datetime.now() - datetime.timedelta(hours=1)
            back_compatible_zone = "us-east-1e"
            for zone in [
                    z for z in ec2_conn.get_all_zones() if z.state == 'available']:
                # Non EC2 clouds may not support get_spot_price_history
                if instance_type is None or cloud_type != 'ec2':
                    zones.append(zone.name)
                elif ec2_conn.get_spot_price_history(instance_type=instance_type,
                                                     end_time=in_the_past.isoformat(),
                                                     availability_zone=zone.name):
                    zones.append(zone.name)
            # Higher-lettered zones seem to have more availability currently
            zones.sort(reverse=True)
            if back_compatible_zone in zones:
                zones = [back_compatible_zone] + \
                    [z for z in zones if z != back_compatible_zone]
            if len(zones) == 0:
                response['error'] = f"Did not find availabilty zone for {instance_type}"
                bioblend.log.error(response['error'])
                zones.append(back_compatible_zone)
        return response

    def _checkURL(self, url):
        """
        Check if the ``url`` is *alive* (i.e., remote server returns code 200(OK)
        or 401 (unauthorized)).
        """
        try:
            p = urlparse(url)
            h = HTTPConnection(p[1])
            h.putrequest('HEAD', p[2])
            h.endheaders()
            r = h.getresponse()
            # CloudMan UI is pwd protected so include 401
            if r.status in (200, 401):
                return True
        except Exception:
            # No response or no good response
            pass
        return False
