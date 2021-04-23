"""
Contains possible interaction dealing with Galaxy users.

Most of these methods must be executed by a registered Galaxy admin user.
"""
from bioblend.galaxy.client import Client


class UserClient(Client):
    module = 'users'

    def __init__(self, galaxy_instance):
        super().__init__(galaxy_instance)

    def get_users(self, deleted=False, f_email=None, f_name=None, f_any=None):
        """
        Get a list of all registered users. If ``deleted`` is set to ``True``,
        get a list of deleted users.

        :type deleted: bool
        :param deleted: Whether to include deleted users


        :type f_email: str
        :param f_email: filter for user emails. The filter will be active for
            non-admin users only if the Galaxy instance has the
            ``expose_user_email`` option set to ``true`` in the
            ``config/galaxy.yml`` configuration file.

        :type f_name: str
        :param f_name: filter for user names. The filter will be active for
            non-admin users only if the Galaxy instance has the
            ``expose_user_name`` option set to ``true`` in the
            ``config/galaxy.yml`` configuration file.

        :type f_any: str
        :param f_any: filter for user email or name. Each filter will be active
            for non-admin users only if the Galaxy instance has the
            corresponding ``expose_user_*`` option set to ``true`` in the
            ``config/galaxy.yml`` configuration file.

        :rtype: list
        :return: a list of dicts with user details.
                 For example::

                   [{'email': 'a_user@example.com',
                     'id': 'dda47097d9189f15',
                     'url': '/api/users/dda47097d9189f15'}]

        """
        params = {}
        if f_email:
            params['f_email'] = f_email
        if f_name:
            params['f_name'] = f_name
        if f_any:
            params['f_any'] = f_any
        return self._get(deleted=deleted, params=params)

    def show_user(self, user_id, deleted=False):
        """
        Display information about a user.

        :type user_id: str
        :param user_id: encoded user ID

        :type deleted: bool
        :param deleted: whether to return results for a deleted user

        :rtype: dict
        :return: a dictionary containing information about the user
        """
        return self._get(id=user_id, deleted=deleted)

    def create_remote_user(self, user_email):
        """
        Create a new Galaxy remote user.

        .. note::
          For this method to work, the Galaxy instance must have the
          ``allow_user_creation`` and ``use_remote_user`` options set to
          ``true`` in the ``config/galaxy.yml`` configuration file. Also
          note that setting ``use_remote_user`` will require an upstream
          authentication proxy server; however, if you do not have one, access
          to Galaxy via a browser will not be possible.

        :type user_email: str
        :param user_email: email of the user to be created

        :rtype: dict
        :return: a dictionary containing information about the created user
        """
        payload = {}
        payload['remote_user_email'] = user_email
        return self._post(payload)

    def create_local_user(self, username, user_email, password):
        """
        Create a new Galaxy local user.

        .. note::
          For this method to work, the Galaxy instance must have the
          ``allow_user_creation`` option set to ``true`` and
          ``use_remote_user`` option set to ``false`` in the
          ``config/galaxy.yml`` configuration file.

        :type username: str
        :param username: username of the user to be created

        :type user_email: str
        :param user_email: email of the user to be created

        :type password: str
        :param password: password of the user to be created

        :rtype: dict
        :return: a dictionary containing information about the created user
        """
        payload = {}
        payload['username'] = username
        payload['email'] = user_email
        payload['password'] = password
        return self._post(payload)

    def get_current_user(self):
        """
        Display information about the user associated with this Galaxy
        connection.

        :rtype: dict
        :return: a dictionary containing information about the current user
        """
        url = self._make_url() + '/current'
        return self._get(url=url)

    def create_user_apikey(self, user_id):
        """
        Create a new API key for a given user.

        :type user_id: str
        :param user_id: encoded user ID

        :rtype: str
        :return: the API key for the user
        """
        url = self._make_url(user_id) + '/api_key'
        payload = {}
        payload['user_id'] = user_id
        return self._post(payload, url=url)

    def delete_user(self, user_id, purge=False):
        """
        Delete a user.

        .. note::
          For this method to work, the Galaxy instance must have the
          ``allow_user_deletion`` option set to ``true`` in the
          ``config/galaxy.yml`` configuration file.

        :type user_id: str
        :param user_id: encoded user ID

        :type purge: bool
        :param purge: if ``True``, also purge (permanently delete) the history

        :rtype: dict
        :return: a dictionary containing information about the deleted user
        """
        params = {}
        if purge is True:
            params['purge'] = purge
        return self._delete(id=user_id, params=params)

    def get_user_apikey(self, user_id):
        """
        Get the current API key for a given user.

        :type user_id: str
        :param user_id: encoded user ID

        :rtype: str
        :return: the API key for the user
        """
        url = self._make_url(user_id) + '/api_key/inputs'
        return self._get(url=url)['inputs'][0]['value']

    def update_user(self, user_id, **kwds):
        """
        Update user information. Some of the attributes that can be
        modified are documented below.

        :type user_id: str
        :param user_id: encoded user ID

        :type username: str
        :param username: Replace user name with the given string

        :type email: str
        :param email: Replace user email with the given string

        :rtype: dict
        :return: details of the updated user
        """
        url = self._make_url(user_id) + '/information/inputs'
        return self._put(url=url, payload=kwds, id=user_id)
