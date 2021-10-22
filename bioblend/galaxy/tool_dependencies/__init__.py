"""
Contains interactions dealing with Galaxy dependency resolvers.
"""
from bioblend.galaxy.client import Client


class ToolDependenciesClient(Client):
    module = 'dependency_resolvers'

    def __init__(self, galaxy_instance):
        super().__init__(galaxy_instance)

    def summarize_toolbox(self, index=None, tool_ids=None, resolver_type=None, include_containers=False, container_type=None, index_by='requirements'):
        """
        Summarize requirements across toolbox (for Tool Management grid).

        :type index: int
        :param index: index of the dependency resolver with respect to
            the dependency resolvers config file

        :type tool_ids: list
        :param tool_ids: tool_ids to return when index_by=tools

        :type resolver_type: str
        :param resolver_type: restrict to specified resolver type

        :type include_containers: bool
        :param include_containers: include container resolvers in resolution

        :type container_type: str
        :param container_type: restrict to specified container type

        :type index_by: str
        :param index_by: By default results are grouped by requirements.  Set to 'tools'
          to return one entry per tool.

        :rtype: list of dicts
        :returns: dictified descriptions of the dependencies, with attribute
          `dependency_type: None` if no match was found.
          For example::

            [{'requirements': [{'name': 'galaxy_sequence_utils',
                                'specs': [],
                                'type': 'package',
                                'version': '1.1.4'},
                               {'name': 'bx-python',
                                'specs': [],
                                'type': 'package',
                                'version': '0.8.6'}],
              'status': [{'cacheable': False,
                          'dependency_type': None,
                          'exact': True,
                          'model_class': 'NullDependency',
                          'name': 'galaxy_sequence_utils',
                          'version': '1.1.4'},
                          {'cacheable': False,
                          'dependency_type': None,
                          'exact': True,
                          'model_class': 'NullDependency',
                          'name': 'bx-python',
                          'version': '0.8.6'}],
              'tool_ids': ['vcf_to_maf_customtrack1']}]

        .. note::
          This method can only be used with Galaxy ``release_20.01`` or later and requires
            the user to be an admin. It relies on an experimental API particularly tied to
            the GUI and therefore is subject to breaking changes.
        """
        assert index_by in ['tools', 'requirements'], "index_by must be one of 'tools' or 'requirements'."
        params = {
            'include_containers': str(include_containers),
            'index_by': index_by,
        }
        if index:
            params['index'] = str(index)
        if tool_ids:
            params['tool_ids'] = ','.join(tool_ids)
        if resolver_type:
            params['resolver_type'] = resolver_type
        if container_type:
            params['container_type'] = container_type

        url = '/'.join((self._make_url(), 'toolbox'))
        return self._get(url=url, params=params)
