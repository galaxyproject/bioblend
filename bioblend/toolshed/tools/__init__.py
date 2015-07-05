"""
Interaction with a Tool Shed instance tools
"""
from bioblend.galaxy.client import Client


class ToolShedClient(Client):

    def __init__(self, toolshed_instance):
        self.module = 'tools'
        super(ToolShedClient, self).__init__(toolshed_instance)

    def search_tools(self, q, page=1, page_size=10):
        """
        Search for tools in a Galaxy Tool Shed

        :type  q: str
        :param q: query string for searching purposes

        :type  page: str
        :param page: page requested

        :type  page_size: str
        :param page_size: page size requested

        :rtype:  dict
        :return: dictionary containing search hits as well as metadata
                for the search
        """
        params = dict(q=q, page=page, page_size=page_size)
        return Client._get(self, params=params)
