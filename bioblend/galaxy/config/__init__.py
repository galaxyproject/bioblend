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
        Get a list of attributes about the Galaxy instance. More attributes will
        be present if the user is an admin.

        :rtype: list
        :return: A list of attributes.
          For example::

            {u'allow_library_path_paste': False,
             u'allow_user_creation': True,
             u'allow_user_dataset_purge': True,
             u'allow_user_deletion': False,
             u'enable_unique_workflow_defaults': False,
             u'ftp_upload_dir': u'/SOMEWHERE/galaxy/ftp_dir',
             u'ftp_upload_site': u'galaxy.com',
             u'library_import_dir': u'None',
             u'logo_url': None,
             u'support_url': u'https://galaxyproject.org/support',
             u'terms_url': None,
             u'user_library_import_dir': None,
             u'wiki_url': u'https://galaxyproject.org/'}
        """
        return self._get()

    def get_version(self):
        """
        Get the current version of the Galaxy instance.
        This functionality is available since Galaxy ``release_15.03``.

        :rtype: dict
        :return: Version of the Galaxy instance

        For example::

            {'extra': {}, 'version_major': '17.01'}
        """
        url = self.gi._make_url(self, None)
        url = url.rstrip('configuration') + 'version'
        return self._get(url=url)
