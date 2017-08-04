"""
Contains possible interactions with the Galaxy Roles
"""
from bioblend.galaxy.client import Client


class RolesClient(Client):

    def __init__(self, galaxy_instance):
        self.module = 'roles'
        super(RolesClient, self).__init__(galaxy_instance)

    def get_roles(self):
        """
        Displays a collection (list) of roles.

        :rtype: list
        :return: A list of dicts with details on individual roles.
          For example::

            [{"id": "f2db41e1fa331b3e",
              "model_class": "Role",
              "name": "Foo",
              "url": "/api/roles/f2db41e1fa331b3e"},
             {"id": "f597429621d6eb2b",
              "model_class": "Role",
              "name": "Bar",
              "url": "/api/roles/f597429621d6eb2b"}]
        """
        return self._get()

    def show_role(self, role_id):
        """
        Display information on a single role

        :type role_id: str
        :param role_id: Encoded role ID

        :rtype: dict
        :return: A description of role
          For example::

            {"description": "Private Role for Foo",
             "id": "f2db41e1fa331b3e",
             "model_class": "Role",
             "name": "Foo",
             "type": "private",
             "url": "/api/roles/f2db41e1fa331b3e"}
        """
        return self._get(id=role_id)

    def create_role(self, role_name, description, user_ids=[], group_ids=[]):
        """
        Create a new role.

        :type role_name: str
        :param role_name: A name for the new role

        :type description: str
        :param description: Description for the new role

        :type user_ids: list
        :param user_ids: A list of encoded user IDs to add to the new role

        :type group_ids: list
        :param group_ids: A list of encoded group IDs to add to the new role

        :rtype: list
        :return: A (size 1) list with newly created role
          details, like::

            [{u'description': u'desc',
              u'url': u'/api/roles/ebfb8f50c6abde6d',
              u'model_class': u'Role',
              u'type': u'admin',
              u'id': u'ebfb8f50c6abde6d',
              u'name': u'Foo'}]
        """
        payload = {
            'name': role_name,
            'description': description,
            'user_ids': user_ids,
            'group_ids': group_ids
        }
        return self._post(payload)
