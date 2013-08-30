"""
Interaction with a Galaxy Tool Shed
"""
from bioblend.galaxy.client import Client


class ToolShedClient(Client):

    def __init__(self, galaxy_instance):
        self.module = 'tool_shed_repositories'
        super(ToolShedClient, self).__init__(galaxy_instance)

    def get_repositories(self):
        """
        Get a list of all repositories in the Tool Shed

        :rtype: list
        :return: Returns a list of dictionaries containing information about
                 repositories present in the Tool Shed.
                 For example::

                   [{u'changeset_revision': u'4afe13ac23b6',
                   u'deleted': False,
                   u'dist_to_shed': False,
                   u'error_message': u'',
                   u'name': u'velvet_toolsuite',
                   u'owner': u'edward-kirton',
                   u'status': u'Installed'}]

        .. versionchanged:: 0.4.1
            Changed method name from ``get_tools`` to ``get_repositories`` to
            better align with the Tool Shed concepts
        """
        return Client._get(self)

    def show_repository(self, toolShed_id):
        """
        Display information of a repository from the Tool Shed

        :type toolShed_id: string
        :param toolShed_id: Encoded toolShed ID

        :rtype: dictionary
        :return: Information about the tool
                 For example::

                   {u'changeset_revision': u'b17455fb6222',
                   u'ctx_rev': u'8',
                   u'owner': u'aaron',
                   u'status': u'Installed',
                   u'url': u'/api/tool_shed_repositories/82de4a4c7135b20a'}

        .. versionchanged:: 0.4.1
            Changed method name from ``show_tool`` to ``show_repository`` to
            better align with the Tool Shed concepts
        """
        return Client._get(self, id=toolShed_id)
