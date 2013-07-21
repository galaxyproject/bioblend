"""
Interaction with Galaxy Tool shed Instance

"""
from bioblend.galaxy.client import Client
from os.path import basename


class ToolShedClient(Client):

    def __init__(self, toolshed_instance):
        self.module = 'repositories'
        super(ToolShedClient, self).__init__(toolshed_instance)


    def get_tools(self):
        """
        Get a list of all tools in galaxy tool shed repository

        :rtype: list
        :return: Returns a list of dictionaries containing information about tools present in the tool shed repositories.
                 For example::
                 [{u'times_downloaded': 0, u'user_id': u'5cefd48bc04af6d4',
                 u'description': u'Order Contigs', u'deleted': False,
                 u'deprecated': False, u'private': False,
                 u'url': u'/api/repositories/287bd69f724b99ce',
                 u'owner': u'billybob', u'id': u'287bd69f724b99ce',
                 u'name': u'best_tool_ever'}]

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
                 {{u'times_downloaded': 0, u'user_id': u'5cefd48bc04af6d4',
                 u'description': u'Order Contigs', u'deleted': False,
                 u'deprecated': False, u'private': False,
                 u'url': u'/api/repositories/287bd69f724b99ce',
                 u'owner': u'billybob', u'id': u'287bd69f724b99ce',
                 u'name': u'best_tool_ever'}
        """
        return Client._get(self, id=toolShed_id)



    def get_ordered_installable_revisions(self,name,owner):
        """
        Returns the ordered list of changeset revision hash strings that are associated
        with installable revisions.  As in the changelog, the list is ordered oldest to newest.

        :type name: string
        :param name: the name of the repository

        :type owner: string
        :param owner: the owner of the repository

        
        :rtype: list
        :return: Information about the tool

        """
        url = self.url + '/get_ordered_installable_revisions'
        params = {}
        params['name'] = name
        params['owner'] = owner
        r= Client._get(self,url,params)
        
        return r.text

    
