"""
Contains possible interactions with the Galaxy Groups
"""
from bioblend.galaxy.client import Client


class GroupsClient(Client):

    def __init__(self, galaxy_instance):
        self.module = 'groups'
        super(GroupsClient, self).__init__(galaxy_instance)

    def get_groups(self):
        """
        Get all (not deleted) groups.

        :rtype: list
        :return: A list of dicts with details on individual groups.
                 For example::

                   [ {"name": "Listeria", "url": "/api/groups/33abac023ff186c2",
                   "model_class": "Group", "id": "33abac023ff186c2"},
                   {"name": "LPN", "url": "/api/groups/73187219cd372cf8",
                   "model_class": "Group", "id": "73187219cd372cf8"}
                   ]


        """
        return Client._get(self)

    def show_group(self, group_id):
        """
        Get details of a given group.

        :type group_id: str
        :param group_id: Encoded group ID

        :rtype: dict
        :return: A description of group
                 For example::

                   {"roles_url": "/api/groups/33abac023ff186c2/roles",
                   "name": "Listeria", "url": "/api/groups/33abac023ff186c2",
                   "users_url": "/api/groups/33abac023ff186c2/users",
                   "model_class": "Group", "id": "33abac023ff186c2"}

        """

        return Client._get(self, id=group_id)

    def create_group(self, group_name, user_ids=[], role_ids=[]):
        """
        Create a new group.

        :type group_name: str
        :param group_name: A name for the new group

        :type user_ids: list
        :param user_ids: A list of encoded user IDs to add to the new group

        :type role_ids: list
        :param role_ids: A list of encoded role IDs to add to the new group

        :rtype: list
        :return: A (size 1) list with newly created group
                 details, like::

                    [{u'id': u'7c9636938c3e83bf',
                      u'model_class': u'Group',
                      u'name': u'My Group Name',
                      u'url': u'/api/groups/7c9636938c3e83bf'}]
        """
        payload = {}
        payload['name'] = group_name
        payload['user_ids'] = user_ids
        payload['role_ids'] = role_ids
        return Client._post(self, payload)

    def update_group(self, group_id, group_name=None, user_ids=[], role_ids=[]):
        """
        Update a group.

        :type group_id: str
        :param group_id: Encoded group ID

        :type group_name: str
        :param group_name: A new name for the group. If None, the group name is
          not changed.

        :type user_ids: list
        :param user_ids: New list of encoded user IDs for the group. It will
          substitute the previous list of users (with [] if not specified)

        :type role_ids: list
        :param role_ids: New list of encoded role IDs for the group. It will
          substitute the previous list of roles (with [] if not specified)

        :rtype: int
        :return: status code
        """
        payload = {}
        payload['name'] = group_name
        payload['user_ids'] = user_ids
        payload['role_ids'] = role_ids
        return Client._put(self, payload, id=group_id).status_code

    def get_group_users(self, group_id):
        """
        Get the list of users associated to the given group.

        :type group_id: str
        :param group_id: Encoded group ID

        :rtype: list of dicts
        :return: List of group users' info
        """
        url = '/'.join([self.gi._make_url(self, group_id), 'users'])
        return Client._get(self, url=url)

    def get_group_roles(self, group_id):
        """
        Get the list of roles associated to the given group.

        :type group_id: str
        :param group_id: Encoded group ID

        :rtype: list of dicts
        :return: List of group roles' info
        """
        url = '/'.join([self.gi._make_url(self, group_id), 'roles'])
        return Client._get(self, url=url)

    def add_group_user(self, group_id, user_id):
        """
        Add a user to the given group.

        :type group_id: str
        :param group_id: Encoded group ID

        :type user_id: str
        :param user_id: Encoded user ID to add to the group

        :rtype: dict
        :return: Added group user's info
        """
        url = '/'.join([self.gi._make_url(self, group_id), 'users', user_id])
        return Client._put(self, dict(), url=url).json()

    def add_group_role(self, group_id, role_id):
        """
        Add a role to the given group.

        :type group_id: str
        :param group_id: Encoded group ID

        :type role_id: str
        :param role_id: Encoded role ID to add to the group

        :rtype: dict
        :return: Added group role's info
        """
        url = '/'.join([self.gi._make_url(self, group_id), 'roles', role_id])
        return Client._put(self, {}, url=url).json()

    def delete_group_user(self, group_id, user_id):
        """
        Remove a user from the given group.

        :type group_id: str
        :param group_id: Encoded group ID

        :type user_id: str
        :param user_id: Encoded user ID to remove from the group
        """
        url = '/'.join([self.gi._make_url(self, group_id), 'users', user_id])
        return Client._delete(self, {}, url=url)

    def delete_group_role(self, group_id, role_id):
        """
        Remove a role from the given group.

        :type group_id: str
        :param group_id: Encoded group ID

        :type role_id: str
        :param role_id: Encoded role ID to remove from the group
        """
        url = '/'.join([self.gi._make_url(self, group_id), 'roles', role_id])
        return Client._delete(self, {}, url=url)
