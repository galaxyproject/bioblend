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
        Displays a collection (list) of groups.


        :rtype: list
        :return: A list of dicts with details on individual groups.
                 For example::

                   [ {"roles_url": "/api/groups/33abac023ff186c2/roles",
                   "name": "Listeria", "url": "/api/groups/33abac023ff186c2",
                   "users_url": "/api/groups/33abac023ff186c2/users",
                   "model_class": "Group", "id": "33abac023ff186c2"},
                   {"roles_url": "/api/groups/73187219cd372cf8/roles",
                   "name": "LPN", "url": "/api/groups/73187219cd372cf8",
                   "users_url": "/api/groups/73187219cd372cf8/users",
                   "model_class": "Group", "id": "73187219cd372cf8"}
                   ]


        """
        return Client._get(self)

    def show_group(self, group_id):
        """
        Display information on a single group

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
        Create a new Galaxy group

        :type group_name: str
        :param group_name: A name for new group

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
