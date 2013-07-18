"""
Interaction with Galaxy Tool shed

"""
from bioblend.galaxy.client import Client
from os.path import basename


class ToolShedClient(Client):

    def __init__(self, galaxy_instance):
        self.module = 'tool_shed_repositories'
        super(ToolShedClient, self).__init__(galaxy_instance)

    def get_tools(self):
        """
        Get a list of all tools in galaxy tool shed repository

        :rtype: list
        :return: Returns a list of dictionaries containing information about tools present in the tool shed repositories.
                 For example::
                 [{u'changeset_revision': u'4afe13ac23b6',
                 u'deleted': False,
                 u'dist_to_shed': False,
                 u'error_message': u'',
                 u'name': u'velvet_toolsuite',
                 u'owner': u'edward-kirton',
                 u'status': u'Installed'}]

        """
        return Client._get(self)
        
    def show_tool(self, toolShed_id):
        """
        Display information of a tool from tool shed

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
        """
        return Client._get(self, id=toolShed_id)

