"""
Interaction with a Tool Shed instance
"""
from bioblend.galaxy.client import Client


class ToolShedClient(Client):

    def __init__(self, toolshed_instance):
        self.module = 'repositories'
        super(ToolShedClient, self).__init__(toolshed_instance)

    def get_repositories(self):
        """
        Get a list of all the repositories in a Galaxy Tool Shed

        :rtype: list
        :return: Returns a list of dictionaries containing information about
                 repositories present in the Tool Shed.
                 For example::

                     [{u'times_downloaded': 0, u'user_id': u'5cefd48bc04af6d4',
                     u'description': u'Order Contigs', u'deleted': False,
                     u'deprecated': False, u'private': False,
                     u'url': u'/api/repositories/287bd69f724b99ce',
                     u'owner': u'billybob', u'id': u'287bd69f724b99ce',
                     u'name': u'best_tool_ever'}]

        .. versionchanged:: 0.4.1
            Changed method name from ``get_tools`` to ``get_repositories`` to
            better align with the Tool Shed concepts
        """
        return Client._get(self)

    def show_repository(self, toolShed_id):
        """
        Display information of a repository from Tool Shed

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

        .. versionchanged:: 0.4.1
            Changed method name from ``show_tool`` to ``show_repository`` to
            better align with the Tool Shed concepts
        """
        return Client._get(self, id=toolShed_id)

    def get_ordered_installable_revisions(self, name, owner):
        """
        Returns the ordered list of changeset revision hash strings that are associated
        with installable revisions.  As in the changelog, the list is ordered oldest to newest.

        :type name: string
        :param name: the name of the repository

        :type owner: string
        :param owner: the owner of the repository

        :rtype: list
        :return: List of changeset revision hash string from oldest to newest

        """
        url = self.url + '/get_ordered_installable_revisions'
        params = {}
        params['name'] = name
        params['owner'] = owner
        r = Client._get(self, url=url, params=params)

        return r

    def get_repository_revision_install_info(self, name, owner, changeset_revision):

        """
        Return a list of dictionaries of metadata about a certain changeset
        revision for a single tool.

        :type name: string
        :param name: the name of the repository

        :type owner: string
        :param owner: the owner of the repository

        :type changeset_revision: string
        :param changeset_revision: the changset_revision of the RepositoryMetadata
                                   object associated with the repository

        :rtype: List of dictionaries
        :return: Returns a list of the following dictionaries:
        a dictionary defining the repository
        a dictionary defining the repository revision (RepositoryMetadata)
        a dictionary including the additional information required to install the repository

                 For example::

                     [{u'times_downloaded': 269, u'user_id': u'1de29d50c3c44272', u'description': u'Galaxy Freebayes Bayesian genetic variant detector tool', u'deleted': False, u'deprecated': False, u'private': False, u'long_description': u'Galaxy Freebayes Bayesian genetic variant detector tool originally included in the Galaxy code distribution but migrated to the tool shed.', u'url': u'/api/repositories/491b7a3fddf9366f', u'owner': u'devteam', u'id': u'491b7a3fddf9366f', u'name': u'freebayes'},
                     {u'repository_id': u'491b7a3fddf9366f', u'has_repository_dependencies': False, u'includes_tools_for_display_in_tool_panel': True, u'url': u'/api/repository_revisions/504be8aaa652c154', u'malicious': False, u'includes_workflows': False, u'downloadable': True, u'includes_tools': True, u'changeset_revision': u'd291dc763c4c', u'id': u'504be8aaa652c154', u'includes_tool_dependencies': True, u'includes_datatypes': False}, {u'freebayes': [u'Galaxy Freebayes Bayesian genetic variant detector tool', u'http://takadonet@toolshed.g2.bx.psu.edu/repos/devteam/freebayes', u'd291dc763c4c', u'9', u'devteam', {},
                     {u'freebayes/0.9.6_9608597d12e127c847ae03aa03440ab63992fedf': {u'repository_name': u'freebayes', u'name': u'freebayes', u'readme': u'\nFreeBayes requires g++ and the standard C and C++ development libraries.\nAdditionally, cmake is required for building the BamTools API.\n        ', u'version': u'0.9.6_9608597d12e127c847ae03aa03440ab63992fedf', u'repository_owner': u'devteam', u'changeset_revision': u'd291dc763c4c', u'type': u'package'}, u'samtools/0.1.18': {u'repository_name': u'freebayes', u'name': u'samtools', u'readme': u'\nCompiling SAMtools requires the ncurses and zlib development libraries.\n        ', u'version': u'0.1.18', u'repository_owner': u'devteam', u'changeset_revision': u'd291dc763c4c', u'type': u'package'}}]}]

        """

        url = self.url + '/get_repository_revision_install_info'
        params = {}
        params['name'] = name
        params['owner'] = owner
        params['changeset_revision'] = changeset_revision

        return Client._get(self, url=url, params=params)

    def repository_revisions(self, downloadable=None, malicious=None,
            tools_functionally_correct=None, missing_test_components=None,
            do_not_test=None, includes_tools=None, test_install_error=None,
            skip_tool_test=None):
        """
        Returns a (possibly filtered) list of dictionaries that include information
        about all repository revisions.  The following parameters can be used to
        filter the list.

        :type downloadable: Boolean
        :param downloadable: Can the tool be downloaded

        :type malicious: Boolean
        :param malicious:

        :type tools_functionally_correct: Boolean
        :param tools_functionally_correct:

        :type missing_test_components: Boolean
        :param missing_test_components:

        :type do_not_test: Boolean
        :param do_not_test:

        :type includes_tools: Boolean
        :param includes_tools:

        :type test_install_error: Boolean
        :param test_install_error:

        :type skip_tool_test: Boolean
        :param skip_tool_test:

        :rtype: List of dictionaries
        :return: Returns a (possibly filtered) list of dictionaries that include
                 information about all repository revisions.
                 For example::

                     [{u'repository_id': u'78f2604ff5e65707', u'has_repository_dependencies': False, u'includes_tools_for_display_in_tool_panel': True, u'url': u'/api/repository_revisions/92250afff777a169', u'malicious': False, u'includes_workflows': False, u'downloadable': True, u'includes_tools': True, u'changeset_revision': u'6e26c5a48e9a', u'id': u'92250afff777a169', u'includes_tool_dependencies': False, u'includes_datatypes': False},
                     {u'repository_id': u'f9662009da7bfce0', u'has_repository_dependencies': False, u'includes_tools_for_display_in_tool_panel': True, u'url': u'/api/repository_revisions/d3823c748ae2205d', u'malicious': False, u'includes_workflows': False, u'downloadable': True, u'includes_tools': True, u'changeset_revision': u'15a54fa11ad7', u'id': u'd3823c748ae2205d', u'includes_tool_dependencies': False, u'includes_datatypes': False}]

        """

        # Not using '_make_url' or '_get' to create url since the module id used
        # to create url is not the same as needed for this method
        url = self.gi.url + '/repository_revisions'
        params = {}

        #nice and long... my god!
        if downloadable:
            params['downloadable'] = 'True'
        if malicious:
            params['malicious'] = 'True'
        if tools_functionally_correct:
            params['tools_functionally_correct'] = 'True'
        if missing_test_components:
            params['missing_test_components'] = 'True'
        if do_not_test:
            params['do_not_test'] = 'True'
        if includes_tools:
            params['includes_tools'] = 'True'
        if test_install_error:
            params['test_install_error'] = 'True'
        if skip_tool_test:
            params['skip_tool_test'] = 'True'

        return Client._get(self, url=url, params=params)

    def show_repository_revision(self, metadata_id):
        '''
        Returns a dictionary that includes information about a specified repository
        revision.

        :type metadata_id: string
        :param metadata_id: Encoded repository metadata ID

        :rtype: dictionary
        :return: Returns a dictionary that includes information about a specified
                 repository revision.
                 For example::

                     {u'repository_id': u'491b7a3fddf9366f',
                      u'has_repository_dependencies': False,
                      u'includes_tools_for_display_in_tool_panel': True,
                      u'test_install_error': False,
                      u'url': u'/api/repository_revisions/504be8aaa652c154',
                      u'malicious': False,
                      u'includes_workflows': False,
                      u'id': u'504be8aaa652c154',
                      u'do_not_test': False,
                      u'downloadable': True,
                      u'includes_tools': True,
                      u'tool_test_results': {u'missing_test_components': [],,
                      u'includes_datatypes': False}

        '''
        # Not using '_make_url' or '_get' to create url since the module id used
        # to create url is not the same as needed for this method
        # since metadata_id has to be defined, easy to create the url here
        url = self.gi.url + '/repository_revisions/' + metadata_id

        return Client._get(self, url=url)
