"""
Interaction with a Tool Shed instance tools
"""
from bioblend.galaxy.client import Client


class ToolShedToolClient(Client):
    module = 'tools'

    def __init__(self, toolshed_instance):
        super().__init__(toolshed_instance)

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

            {'hits': [{'matched_terms': [],
                       'score': 3.0,
                       'tool': {'description': 'convert between various FASTQ quality formats',
                                'id': '69819b84d55f521efda001e0926e7233',
                                'name': 'FASTQ Groomer',
                                'repo_name': None,
                                'repo_owner_username': 'devteam'}},
                      {'matched_terms': [],
                       'score': 3.0,
                       'tool': {'description': 'converts a bam file to fastq files.',
                                'id': '521e282770fd94537daff87adad2551b',
                                'name': 'Defuse BamFastq',
                                'repo_name': None,
                                'repo_owner_username': 'jjohnson'}}],
             'hostname': 'https://testtoolshed.g2.bx.psu.edu/',
             'page': '1',
             'page_size': '2',
             'total_results': '118'}
        """
        params = dict(q=q, page=page, page_size=page_size)
        return self._get(params=params)
