"""
Contains possible interaction dealing with Galaxy configuration.

"""
from bioblend.galaxy.client import Client


class ConfigClient(Client):

    def __init__(self, galaxy_instance):
        self.module = 'configuration'
        super(ConfigClient, self).__init__(galaxy_instance)

    def get_config(self):
        """
        Get a list of attributes about galaxy instance. More attributes will be present if user is an admin


        :rtype: list
        :return: A list of attributes.
                 For example::

                     {   u'allow_library_path_paste': False,u'allow_user_creation': True,
                     u'allow_user_dataset_purge': True,u'allow_user_deletion': False,
                     u'enable_unique_workflow_defaults': False,u'ftp_upload_dir': u'/SOMEWHERE/galaxy/ftp_dir'
                     ,u'ftp_upload_site': u'galaxy.com',u'library_import_dir': u'None',
                     u'logo_url': None,u'support_url': u'http://wiki.g2.bx.psu.edu/Support'
                     ,u'terms_url': None,u'user_library_import_dir': None,u'wiki_url': u'http://g2.trac.bx.psu.edu/'}


        """
        return Client._get(self)
