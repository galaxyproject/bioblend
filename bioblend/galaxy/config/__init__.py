"""
Contains possible interaction dealing with Galaxy configuration.

"""
from bioblend.galaxy.client import Client


class ConfigClient(Client):
    module = 'configuration'

    def __init__(self, galaxy_instance):
        super().__init__(galaxy_instance)

    def get_config(self):
        """
        Get a list of attributes about the Galaxy instance. More attributes will
        be present if the user is an admin.

        :rtype: list
        :return: A list of attributes.
          For example::

            {'allow_library_path_paste': False,
             'allow_user_creation': True,
             'allow_user_dataset_purge': True,
             'allow_user_deletion': False,
             'enable_unique_workflow_defaults': False,
             'ftp_upload_dir': '/SOMEWHERE/galaxy/ftp_dir',
             'ftp_upload_site': 'galaxy.com',
             'library_import_dir': 'None',
             'logo_url': None,
             'support_url': 'https://galaxyproject.org/support',
             'terms_url': None,
             'user_library_import_dir': None,
             'wiki_url': 'https://galaxyproject.org/'}
        """
        return self._get()

    def get_version(self):
        """
        Get the current version of the Galaxy instance.

        :rtype: dict
        :return: Version of the Galaxy instance
          For example::

            {'extra': {}, 'version_major': '17.01'}
        """
        url = self.gi.url + '/version'
        return self._get(url=url)

    def whoami(self):
        """
        Return information about the current authenticated user.

        :rtype: dict
        :return: Information about current authenticated user
          For example::

            {'active': True,
             'deleted': False,
             'email': 'user@example.org',
             'id': '4aaaaa85aacc9caa',
             'last_password_change': '2021-07-29T05:34:54.632345',
             'model_class': 'User',
             'username': 'julia'}
        """
        url = self.gi.url + "/whoami"
        return self._get(url=url)
