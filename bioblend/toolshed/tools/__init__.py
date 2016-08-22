"""
Interaction with a Tool Shed instance tools
"""
from bioblend.galaxy.client import Client


class ToolShedToolClient(Client):

    def __init__(self, toolshed_instance):
        self.module = 'tools'
        super(ToolShedToolClient, self).__init__(toolshed_instance)

    def search_tools(self, q, page=1, page_size=10):
        """
        Search for tools in a Galaxy Tool Shed.

        :type q: str
        :param q: query string for searching purposes

        :type page: int
        :param page: page requested

        :type page_size: int
        :param page_size: page size requested

        :rtype: dict
        :return: dictionary containing search hits as well as metadata for the
          search. For example::

            {u'hits': [{u'matched_terms': [],
               u'score': 3.0,
               u'tool': {u'description': u'convert between various FASTQ quality formats',
                u'id': u'69819b84d55f521efda001e0926e7233',
                u'name': u'FASTQ Groomer',
                u'repo_name': None,
                u'repo_owner_username': u'devteam'}},
              {u'matched_terms': [],
               u'score': 3.0,
               u'tool': {u'description': u'converts a bam file to fastq files.',
                u'id': u'521e282770fd94537daff87adad2551b',
                u'name': u'Defuse BamFastq',
                u'repo_name': None,
                u'repo_owner_username': u'jjohnson'}}],
             u'hostname': u'https://testtoolshed.g2.bx.psu.edu/',
             u'page': u'1',
             u'page_size': u'2',
             u'total_results': u'118'}
        """
        params = dict(q=q, page=page, page_size=page_size)
        return self._get(params=params)
