"""
Contains possible interaction dealing with Galaxy users.

These methods must be executed by a registered Galaxy admin user.
"""
from blend.galaxy.client import Client


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
        """
        return Client._get(self, id=user_id, deleted=deleted)

    def create_user(self, user_email):
        """
        Create a new Galaxy user.

        .. note::
            For this method to work, the Galaxy instance must have
            ``allow_user_creation`` and ``use_remote_user`` options set to ``True``
            in the ``universe_wsgi.ini`` configuration file. Also note that setting
            ``use_remote_user`` will require an upstream authentication proxy
            server; however, if you do not have one, access to Galaxy via a browser
            will not be possible.
        """
        payload = {}
        payload['remote_user_email'] = user_email
        return Client._post(self, payload)
