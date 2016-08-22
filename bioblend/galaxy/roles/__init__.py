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
