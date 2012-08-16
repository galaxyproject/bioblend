"""
Setup and launch a CloudMan instance.
"""
import datetime
from httplib import HTTP
from urlparse import urlparse

import boto
from boto.ec2.regioninfo import RegionInfo
from boto.exception import EC2ResponseError

import blend

# Comment the following line if no loggin at the prompt is desired
#blend.set_stream_logger(__name__)


class Bunch(object):
    """
    A convenience class to allow dict keys to be representes as object fields.

    The end result is that this allows a dict to be to be represented the same
    as a database class, thus the two become interchangeable as a data source.
    """
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def __repr__(self):
        """
        Return the contents of the dict in a printable representation
        """
        return str(self.__dict__)


class CloudManLaunch(object):
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
            self.cloud = Bunch(
                    id='1',  # for compatiility w/ DB representation
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
                    s3_conn_path='/',
            )
        else:
            self.cloud = cloud
        self.ec2_conn = self.connect_ec2(self.access_key, self.secret_key, self.cloud)
        self.instance_id = None  # To be set after an instance has been launched
        self.rs = None  # boto ResultSet object - to be set after an instance has been launched

    def __repr__(self):
        return "Cloud: {0}; acct ID: {1}".format(self.cloud.name, self.access_key)

    def launch(self, cluster_name, image_id, instance_type, password,
               kernel_id=None, ramdisk_id=None, key_name='cloudman_key_pair',
               security_groups=['CloudMan'], placement='', **kwargs):
        """
        Check all the prerequisites (key pair and security groups) for
        launching a CloudMan instance, compose the user data based on the
        parameters specified in the arguments and the cloud properties as
        defined in the object's ``cloud`` field.

        For the current list of user data fields that can be provided via
        ``kwargs``, see `<http://wiki.g2.bx.psu.edu/CloudMan/UserData>`_

        Return a dict containing the properties and info with wich an instance
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
        ret = {'sg_names': [],
               'kp_name': '',
               'kp_material': '',
               'rs': '',
               'instance_id': '',
               'error': ''}
        # First satisfy the prerequisites
        for sg in security_groups:
            ret['sg_names'].append(self.create_cm_security_group(sg))
        ret['kp_name'], ret['kp_material'] = self.create_key_pair(key_name)
        # If not provided, find placement - see the method for potential issues!
        if placement == '':
            placement = self._find_placements(self.ec2_conn, instance_type,
                    self.cloud.cloud_type)[0]
        # Compose user data for launching an instance, ensuring we have the required fields
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
                                        user_data=ud,
                                        kernel_id=kernel_id,
                                        ramdisk_id=ramdisk_id,
                                        placement=placement)
            ret['rs'] = rs
        except EC2ResponseError, e:
            err = "Problem launching an instance: %s" % e
            blend.log.error(err)
            ret['error'] = err
        if rs:
            try:
                blend.log.info("Launched an instance with ID %s" % rs.instances[0].id)
                ret['instance_id'] = rs.instances[0].id
                ret['instance_ip'] = rs.instances[0].ip_address
                # Store some of this data locally for easier state updates
                self.rs = rs
                self.instance_id = rs.instances[0].id
            except Exception, e:
                err = "Problem with the launched instance object: %s" % e
                blend.log.error(err)
                ret['error'] = err
        else:
            err = "Problem launching an instance?"
            blend.log.warning(err)
            ret['error'] = err
        return ret

    def create_cm_security_group(self, sg_name='CloudMan'):
        """
        Create a security group with all authorizations required to run CloudMan.
        If the group already exists, check its rules and add the missing ones.
        Return the name of the created security group.
        """
        cmsg = None
        # Check if this security group already exists
        sgs = self.ec2_conn.get_all_security_groups()
        for sg in sgs:
            if sg.name == sg_name:
                cmsg = sg
                blend.log.debug("Security group '%s' already exists; will add authorizations next." % sg_name)
                break
        # If it does not exist, create security group
        if cmsg is None:
            blend.log.debug("Creating Security Group %s" % sg_name)
            cmsg = self.ec2_conn.create_security_group(sg_name, 'A security group for CloudMan')
        # Add appropriate authorization rules
        # If these rules already exist, nothing will be changed in the SG
        ports = (('80', '80'),  # Web UI
                 ('20', '21'),  # FTP
                 ('22', '22'),  # ssh
                 ('30000', '30100'),  # FTP transfer
                 ('42284', '42284'))  # CloudMan UI
        for port in ports:
            try:
                if not self.rule_exists(cmsg.rules, from_port=port[0], to_port=port[1]):
                    cmsg.authorize(ip_protocol='tcp', from_port=port[0], to_port=port[1], cidr_ip='0.0.0.0/0')
                else:
                    blend.log.debug("Rule (%s:%s) already exists in the SG" % (port[0], port[1]))
            except EC2ResponseError, e:
                blend.log.error("A problem with security group authorizations: %s" % e)
        # Add rule that allows communication between instances in the same SG
        g_rule_exists = False  # Flag to indicate if group rule already exists
        ci = self._get_cloud_info(self.cloud)
        cloud_type = ci['cloud_type']
        cidr_range = ci.get('cidr_range', '')
        # AWS allows grants to be named, thus allowing communication within a group.
        # Other cloud middlewares do now support that functionality so resort to CIDR grant.
        if cloud_type == 'ec2':
            for rule in cmsg.rules:
                for grant in rule.grants:
                    if grant.name == cmsg.name:
                        g_rule_exists = True
                        blend.log.debug("Group rule already exists in the SG")
                if g_rule_exists:
                    break
        else:
            for rule in cmsg.rules:
                for grant in rule.grants:
                    if grant.cidr_ip == cidr_range:
                        g_rule_exists = True
                        blend.log.debug("Group rule already exists in the SG")
                    if g_rule_exists:
                        break
        if g_rule_exists is False:
            try:
                if cloud_type == 'ec2':
                    cmsg.authorize(src_group=cmsg)
                else:
                    cmsg.authorize(ip_protocol='tcp', from_port=1, to_port=65535, cidr_ip=cidr_range)
            except EC2ResponseError, e:
                blend.log.error("A problem w/ security group authorization: %s" % e)
        blend.log.info("Done configuring '%s' security group" % cmsg.name)
        return cmsg.name

    def rule_exists(self, rules, from_port, to_port, ip_protocol='tcp', cidr_ip='0.0.0.0/0'):
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
        Create a key pair with the provided ``key_name``.
        Return the name of the key or ``None`` if there was an error creating the key.
        """
        kp = None
        # Check if a key pair under the given name already exists. If it does not,
        # create it, else return.
        kps = self.ec2_conn.get_all_key_pairs()
        for akp in kps:
            if akp.name == key_name:
                blend.log.debug("Key pair '%s' already exists; not creating it again." % key_name)
                return akp.name, None
        try:
            kp = self.ec2_conn.create_key_pair(key_name)
        except EC2ResponseError, e:
            blend.log.error("Problem creating key pair '%s': %s" % (key_name, e))
            return None, None
        blend.log.info("Created key pair '%s'" % kp.name)
        return kp.name, kp.material

    def get_status(self, instance_id=None, ec2_conn=None):
        """
        Check on the status of an instance. If ``instance_id`` is not provided,
        the ID obtained when launching *the most recent* instance is used. Note
        that this assumes the instance being checked on was launched using this
        class. Also note that the same class may be used to launch multiple instances
        but only the most recent ``instance_id`` is kept while any others will
        need to be explicitly specified.

        This method also allows the required ``ec2_conn`` connection object to be
        provided at invocation time. If the object is not provided, credentials
        defined for the class are used (ability to specify a custom ``ec2_conn``
        helps in case of stateless method invocations).

        Return a ``state`` dict with the current ``instance_state``, ``public_ip``,
        ``placement``, and ``error`` keys, which capture the current state (the
        values for those keys defualt to empty string if no data is available from
        the cloud).
        """
        if ec2_conn is None:
            ec2_conn = self.ec2_conn
        rs = None
        state = {'instance_state': "",
                 'public_ip': "",
                 'placement': "",
                 'error': ""}
        if instance_id is None:
            instance_id = self.instance_id
        # Make sure we have an instance ID
        if instance_id is None:
            err = "Missing instance ID, cannot check the state."
            blend.log.error(err)
            state['error'] = err
            return state
        try:
            rs = ec2_conn.get_all_instances([instance_id])
            if rs is not None:
                inst_state = rs[0].instances[0].update()
                public_ip = rs[0].instances[0].ip_address
                if inst_state == 'running':
                    cm_url = "http://{dns}/cloud".format(dns=public_ip)
                    # Wait until the CloudMan URL is accessible to return the data
                    if self._checkURL(cm_url) is True:
                        state['public_ip'] = public_ip
                        state['instance_state'] = inst_state
                        state['placement'] = rs[0].instances[0].placement
                    else:
                        state['instance_state'] = 'booting'
                else:
                    state['instance_state'] = inst_state
        except Exception, e:
            err = "Problem updating instance '%s' state: %s" % (instance_id, e)
            blend.log.error(err)
            state['error'] = err
        return state

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
                              # api_version is needed for availability zone support for EC2
                              api_version='2012-06-01' if ci['cloud_type'] == 'ec2' else None,
                              is_secure=ci['is_secure'],
                              region=r,
                              port=ci['ec2_port'],
                              path=ci['ec2_conn_path'])
        return ec2_conn

    def _compose_user_data(self, user_provided_data):
        """
        A convenience method used to compose and properly format the user data
        required when requiesting an instance.

        ``user_provided_data`` is the data provided by a user required to identify
        a cluster and user other user requirements.
        """
        form_data = {}
        # Do not include the following fields in the user data but do include
        # any 'advanced startup fields' that might be added in the future
        excluded_fields = ['sg_name', 'image_id', 'instance_id', 'kp_name', 'cloud', 'cloud_type',
            'public_dns', 'cidr_range', 'kp_material', 'placement']
        for key, value in user_provided_data.iteritems():
            if key not in excluded_fields:
                form_data[key] = value
        # If the following user data keys are empty, do not include them in the request user data
        udkeys = ['post_start_script_url', 'worker_post_start_script_url', 'bucket_default', 'share_string']
        for udkey in udkeys:
            if udkey in form_data and form_data[udkey] == '':
                del form_data[udkey]
        # Check if bucket_default is defined for the given cloud and, if it was not
        # provided by the user, add it to the user data. However, do so only if the
        # the value is not blank - blank conflicts with CloudMan's ec2autorun.py
        if 'bucket_default' not in form_data and self.cloud.bucket_default != '':
            form_data['bucket_default'] = self.cloud.bucket_default
        # Reuse the ``password`` for the ``freenxpass`` user data option
        if 'freenxpass' not in form_data and 'password' in form_data:
            form_data['freenxpass'] = form_data['password']
        # Convert form_data into the YAML format
        ud = "\n".join(['%s: %s' % (key, value) for key, value in form_data.iteritems()])
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
            ci = "\n".join(['%s: %s' % (key, value) for key, value in ci.iteritems()])
        return ci

    def _find_placements(self, ec2_conn, instance_type, cloud_type):
        """
        Find an EC2 region zone that supports the requested instance type.

        We do this by checking the spot prices in the potential availability zones
        for support before deciding on a region:
        http://blog.piefox.com/2011/07/ec2-availability-zones-and-instance.html

        If instance_type is None, finds all zones that are currently available.
        
        Note that, currently, this only applies to AWS. For other clouds, all
        the available zones are returned.
        """
        zones = []
        yesterday = datetime.datetime.now() - datetime.timedelta(1)
        back_compatible_zone = "us-east-1b"
        for zone in ec2_conn.get_all_zones():
            if zone.state in ["available"]:
                # Non EC2 clouds may not support get_spot_price_history
                if instance_type is not None and cloud_type == 'ec2':
                    if (len(ec2_conn.get_spot_price_history(instance_type=instance_type,
                                                            end_time=yesterday.isoformat(),
                                                            availability_zone=zone.name)) > 0):
                        zones.append(zone.name)
                else:
                    zones.append(zone.name)
        zones.sort()
        if back_compatible_zone in zones:
            zones = [back_compatible_zone] + [z for z in zones if z != back_compatible_zone] 
        if len(zones) == 0:
            log.error("Did not find availabilty zone in {0} for {1}".format(base, instance_type))
            zones.append(back_compatible_zone)
        return zones

    def _checkURL(self, url):
        """
        Check if the ``url`` is *alive* (i.e., remote server returns code 200(OK)
        or 401 (unauthorized)).
        """
        try:
            p = urlparse(url)
            h = HTTP(p[1])
            h.putrequest('HEAD', p[2])
            h.endheaders()
            r = h.getreply()
            if r[0] == 200 or r[0] == 401:  # CloudMan UI is pwd protected so include 401
                return True
        except Exception:
            # No response or no good response
            pass
        return False
