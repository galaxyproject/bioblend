"""
Contains possible interactions with the Galaxy Groups 
"""
from bioblend.galaxy.client import Client

import shutil
import urllib2

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

        :type group_id: string
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
