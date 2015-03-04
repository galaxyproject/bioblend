"""
Contains possible interaction dealing with Galaxy users.

These methods must be executed by a registered Galaxy admin user.
"""
from bioblend.galaxy.client import Client


class UserClient(Client):

    def __init__(self, galaxy_instance):
        self.module = 'users'
        super(UserClient, self).__init__(galaxy_instance)

    def get_users(self, deleted=False):
        """
        Get a list of all registered users. If ``deleted`` is set to ``True``,
        get a list of deleted users.

        :rtype: list
        :return: A list of dicts with user details.
                 For example::

                   [{u'email': u'a_user@example.com',
                     u'id': u'dda47097d9189f15',
                     u'url': u'/api/users/dda47097d9189f15'}]

        """
        return Client._get(self, deleted=deleted)

    def show_user(self, user_id, deleted=False):
        """
        Display information about a user. If ``deleted`` is set to ``True``,
        display information about a deleted user.

        :type user_id: str
        :param user_id: User ID to inspect

        :type deleted: bool
        :param deleted: Whether to return results for a deleted user

        :rtype: dict
        :return: dictionary containing information about the user
        """
        return Client._get(self, id=user_id, deleted=deleted)

    def create_user(self, user_email):
        """
        Deprecated method.

        Just an alias for create_remote_user().
        """
        return self.create_remote_user(user_email)

    def create_remote_user(self, user_email):
        """
        Create a new Galaxy remote user.

        .. note::
          For this method to work, the Galaxy instance must have the
          ``allow_user_creation`` and ``use_remote_user`` options set to
          ``True`` in the ``config/galaxy.ini`` configuration file. Also
          note that setting ``use_remote_user`` will require an upstream
          authentication proxy server; however, if you do not have one, access
          to Galaxy via a browser will not be possible.

        :type user_email: str
        :param user_email: Email of user to be created

        :rtype: dict
        :return: dictionary containing information about the created user
        """
        payload = {}
        payload['remote_user_email'] = user_email
        return Client._post(self, payload)

    def create_local_user(self, username, user_email, password):
        """
        Create a new Galaxy user.

        .. note::
          For this method to work, the Galaxy instance must have the
          ``allow_user_creation`` option set to ``True`` and
          ``use_remote_user`` option set to ``False`` in the
          ``config/galaxy.ini`` configuration file.

        :type username: str
        :param username: Username of user to be created

        :type user_email: str
        :param user_email: Email of user to be created

        :type password: str
        :param password: password of user to be created

        :rtype: dict
        :return: dictionary containing information about the created user
        """
        payload = {}
        payload['username'] = username
        payload['email'] = user_email
        payload['password'] = password
        return Client._post(self, payload)

    def get_current_user(self):
        """
        Returns the user id associated with this Galaxy connection

        :rtype: dict
        :return: dictionary containing information about the current user
        """
        url = self.gi._make_url(self, None)
        url = '/'.join([url, 'current'])
        return Client._get(self, url=url)

    def create_user_apikey(self, user_id):
        """
        Create a new api key for a user

        :type user_id: str
        :param user_id: Encoded user ID

        :rtype: str
        :return: The api key for the user
        """

        url = self.gi._make_url(self, None)
        url = '/'.join([url, user_id, 'api_key'])
        payload = {}
        payload['user_id'] = user_id

        return Client._post(self, payload, url=url)
