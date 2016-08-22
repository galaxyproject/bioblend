"""
Interaction with a Tool Shed instance repositories
"""
from bioblend.galaxy.client import Client
from bioblend.util import attach_file


class ToolShedRepositoryClient(Client):

    def __init__(self, toolshed_instance):
        self.module = 'repositories'
        super(ToolShedRepositoryClient, self).__init__(toolshed_instance)

    def get_repositories(self):
        """
        Get a list of all the repositories in a Galaxy Tool Shed.

        :rtype: list
        :return: Returns a list of dictionaries containing information about
          repositories present in the Tool Shed.
          For example::

            [{u'category_ids': [u'c1df3132f6334b0e', u'f6d7b0037d901d9b'],
              u'deleted': False,
              u'deprecated': False,
              u'description': u'Order Contigs',
              u'homepage_url': u'',
              u'id': u'287bd69f724b99ce',
              u'name': u'best_tool_ever',
              u'owner': u'billybob',
              u'private': False,
              u'remote_repository_url': u'',
              u'times_downloaded': 0,
              u'type': u'unrestricted',
              u'url': u'/api/repositories/287bd69f724b99ce',
              u'user_id': u'5cefd48bc04af6d4'}]

        .. versionchanged:: 0.4.1
          Changed method name from ``get_tools`` to ``get_repositories`` to
          better align with the Tool Shed concepts.
        """
        return self._get()

    def search_repositories(self, q, page=1, page_size=10):
        """
        Search for repositories in a Galaxy Tool Shed.

        :type  q: str
        :param q: query string for searching purposes

        :type  page: int
        :param page: page requested

        :type  page_size: int
        :param page_size: page size requested

        :rtype:  dict
        :return: dictionary containing search hits as well as metadata for the
          search.
          For example::

            {u'hits': [{u'matched_terms': [],
               u'repository': {u'approved': u'no',
                u'description': u'Convert export file to fastq',
                u'full_last_updated': u'2015-01-18 09:48 AM',
                u'homepage_url': u'',
                u'id': u'bdfa208f0cf6504e',
                u'last_updated': u'less than a year',
                u'long_description': u'This is a simple too to convert Solexas Export files to FASTQ files.',
                u'name': u'export_to_fastq',
                u'remote_repository_url': u'',
                u'repo_owner_username': u'louise',
                u'times_downloaded': 164},
               u'score': 4.92},
              {u'matched_terms': [],
               u'repository': {u'approved': u'no',
                u'description': u'Convert BAM file to fastq',
                u'full_last_updated': u'2015-04-07 11:57 AM',
                u'homepage_url': u'',
                u'id': u'175812cd7caaf439',
                u'last_updated': u'less than a month',
                u'long_description': u'Use Picards SamToFastq to convert a BAM file to fastq. Useful for storing reads as BAM in Galaxy and converting to fastq when needed for analysis.',
                u'name': u'bam_to_fastq',
                u'remote_repository_url': u'',
                u'repo_owner_username': u'brad-chapman',
                u'times_downloaded': 138},
               u'score': 4.14}],
             u'hostname': u'https://testtoolshed.g2.bx.psu.edu/',
             u'page': u'1',
             u'page_size': u'2',
             u'total_results': u'64'}
        """
        params = dict(q=q, page=page, page_size=page_size)
        return self._get(params=params)

    def show_repository(self, toolShed_id):
        """
        Display information of a repository from Tool Shed

        :type toolShed_id: str
        :param toolShed_id: Encoded Tool Shed ID

        :rtype: dict
        :return: Information about the tool.
          For example::

            {u'category_ids': [u'c1df3132f6334b0e', u'f6d7b0037d901d9b'],
             u'deleted': False,
             u'deprecated': False,
             u'description': u'Order Contigs',
             u'homepage_url': u'',
             u'id': u'287bd69f724b99ce',
             u'long_description': u'',
             u'name': u'best_tool_ever',
             u'owner': u'billybob',
             u'private': False,
             u'remote_repository_url': u'',
             u'times_downloaded': 0,
             u'type': u'unrestricted',
             u'url': u'/api/repositories/287bd69f724b99ce',
             u'user_id': u'5cefd48bc04af6d4'}

        .. versionchanged:: 0.4.1
          Changed method name from ``show_tool`` to ``show_repository`` to
          better align with the Tool Shed concepts.
        """
        return self._get(id=toolShed_id)

    def get_ordered_installable_revisions(self, name, owner):
        """
        Returns the ordered list of changeset revision hash strings that are
        associated with installable revisions. As in the changelog, the list is
        ordered oldest to newest.

        :type name: str
        :param name: the name of the repository

        :type owner: str
        :param owner: the owner of the repository

        :rtype: list
        :return: List of changeset revision hash strings from oldest to newest
        """
        url = '/'.join([self.url, 'get_ordered_installable_revisions'])
        params = {
            'name': name,
            'owner': owner
        }
        r = self._get(url=url, params=params)

        return r

    def get_repository_revision_install_info(self, name, owner,
                                             changeset_revision):
        """
        Return a list of dictionaries of metadata about a certain changeset
        revision for a single tool.

        :type name: str
        :param name: the name of the repository

        :type owner: str
        :param owner: the owner of the repository

        :type changeset_revision: str
        :param changeset_revision: the changeset_revision of the
          RepositoryMetadata object associated with the repository

        :rtype: List of dictionaries
        :return: Returns a list of the following dictionaries:

          #. a dictionary defining the repository
          #. a dictionary defining the repository revision (RepositoryMetadata)
          #. a dictionary including the additional information required to
             install the repository

          For example::

                     [{u'deleted': False,
                       u'deprecated': False,
                       u'description': u'Galaxy Freebayes Bayesian genetic variant detector tool',
                       u'homepage_url': u'',
                       u'id': u'491b7a3fddf9366f',
                       u'long_description': u'Galaxy Freebayes Bayesian genetic variant detector tool originally included in the Galaxy code distribution but migrated to the tool shed.',
                       u'name': u'freebayes',
                       u'owner': u'devteam',
                       u'private': False,
                       u'remote_repository_url': u'',
                       u'times_downloaded': 269,
                       u'type': u'unrestricted',
                       u'url': u'/api/repositories/491b7a3fddf9366f',
                       u'user_id': u'1de29d50c3c44272'},
                      {u'changeset_revision': u'd291dc763c4c',
                       u'do_not_test': False,
                       u'downloadable': True,
                       u'has_repository_dependencies': False,
                       u'id': u'504be8aaa652c154',
                       u'includes_datatypes': False,
                       u'includes_tool_dependencies': True,
                       u'includes_tools': True,
                       u'includes_tools_for_display_in_tool_panel': True,
                       u'includes_workflows': False,
                       u'malicious': False,
                       u'repository_id': u'491b7a3fddf9366f',
                       u'url': u'/api/repository_revisions/504be8aaa652c154'},
                      {u'freebayes': [u'Galaxy Freebayes Bayesian genetic variant detector tool',
                        u'http://testtoolshed.g2.bx.psu.edu/repos/devteam/freebayes',
                        u'd291dc763c4c',
                        u'9',
                        u'devteam',
                        {},
                        {u'freebayes/0.9.6_9608597d12e127c847ae03aa03440ab63992fedf': {u'changeset_revision': u'd291dc763c4c',
                          u'name': u'freebayes',
                          u'repository_name': u'freebayes',
                          u'repository_owner': u'devteam',
                          u'type': u'package',
                          u'version': u'0.9.6_9608597d12e127c847ae03aa03440ab63992fedf'},
                         u'samtools/0.1.18': {u'changeset_revision': u'd291dc763c4c',
                          u'name': u'samtools',
                          u'repository_name': u'freebayes',
                          u'repository_owner': u'devteam',
                          u'type': u'package',
                          u'version': u'0.1.18'}}]}]
        """
        url = '/'.join([self.url, 'get_repository_revision_install_info'])
        params = {
            'name': name,
            'owner': owner,
            'changeset_revision': changeset_revision
        }
        return self._get(url=url, params=params)

    def repository_revisions(self, downloadable=None, malicious=None,
                             tools_functionally_correct=None,
                             missing_test_components=None, do_not_test=None,
                             includes_tools=None, test_install_error=None,
                             skip_tool_test=None):
        """
        Returns a (possibly filtered) list of dictionaries that include
        information about all repository revisions. The following parameters can
        be used to filter the list.

        :type downloadable: bool
        :param downloadable: Can the tool be downloaded

        :type malicious: bool
        :param malicious:

        :type tools_functionally_correct: bool
        :param tools_functionally_correct:

        :type missing_test_components: bool
        :param missing_test_components:

        :type do_not_test: bool
        :param do_not_test:

        :type includes_tools: bool
        :param includes_tools:

        :type test_install_error: bool
        :param test_install_error:

        :type skip_tool_test: bool
        :param skip_tool_test:

        :rtype: List of dictionaries
        :return: Returns a (possibly filtered) list of dictionaries that include
          information about all repository revisions.
          For example::

            [{u'changeset_revision': u'6e26c5a48e9a',
              u'do_not_test': False,
              u'downloadable': True,
              u'has_repository_dependencies': False,
              u'id': u'92250afff777a169',
              u'includes_datatypes': False,
              u'includes_tool_dependencies': False,
              u'includes_tools': True,
              u'includes_tools_for_display_in_tool_panel': True,
              u'includes_workflows': False,
              u'malicious': False,
              u'missing_test_components': False,
              u'repository_id': u'78f2604ff5e65707',
              u'test_install_error': False,
              u'time_last_tested': None,
              u'tools_functionally_correct': False,
              u'url': u'/api/repository_revisions/92250afff777a169'},
             {u'changeset_revision': u'15a54fa11ad7',
              u'do_not_test': False,
              u'downloadable': True,
              u'has_repository_dependencies': False,
              u'id': u'd3823c748ae2205d',
              u'includes_datatypes': False,
              u'includes_tool_dependencies': False,
              u'includes_tools': True,
              u'includes_tools_for_display_in_tool_panel': True,
              u'includes_workflows': False,
              u'malicious': False,
              u'missing_test_components': False,
              u'repository_id': u'f9662009da7bfce0',
              u'test_install_error': False,
              u'time_last_tested': None,
              u'tools_functionally_correct': False,
              u'url': u'/api/repository_revisions/d3823c748ae2205d'}]
        """
        # Not using '_make_url' or '_get' to create url since the module id used
        # to create url is not the same as needed for this method
        url = '/'.join([self.gi.url, 'repository_revisions'])
        params = {}
        if downloadable:
            params['downloadable'] = True
        if malicious:
            params['malicious'] = True
        if tools_functionally_correct:
            params['tools_functionally_correct'] = True
        if missing_test_components:
            params['missing_test_components'] = True
        if do_not_test:
            params['do_not_test'] = True
        if includes_tools:
            params['includes_tools'] = True
        if test_install_error:
            params['test_install_error'] = True
        if skip_tool_test:
            params['skip_tool_test'] = True
        return self._get(url=url, params=params)

    def show_repository_revision(self, metadata_id):
        '''
        Returns a dictionary that includes information about a specified
        repository revision.

        :type metadata_id: str
        :param metadata_id: Encoded repository metadata ID

        :rtype: dict
        :return: Returns a dictionary that includes information about a
          specified repository revision.
          For example::

            {u'changeset_revision': u'7602de1e7f32',
             u'do_not_test': False,
             u'downloadable': True,
             u'has_repository_dependencies': False,
             u'id': u'504be8aaa652c154',
             u'includes_datatypes': False,
             u'includes_tool_dependencies': False,
             u'includes_tools': True,
             u'includes_tools_for_display_in_tool_panel': True,
             u'includes_workflows': False,
             u'malicious': False,
             u'missing_test_components': True,
             u'repository_id': u'491b7a3fddf9366f',
             u'test_install_error': False,
             u'time_last_tested': None,
             u'tool_test_results': {u'missing_test_components': []},
             u'tools_functionally_correct': False,
             u'url': u'/api/repository_revisions/504be8aaa652c154'}
        '''
        # Not using '_make_url' or '_get' to create url since the module id used
        # to create url is not the same as needed for this method
        # since metadata_id has to be defined, easy to create the url here
        url = '/'.join([self.gi.url, 'repository_revisions', metadata_id])
        return self._get(url=url)

    def update_repository(self, id, tar_ball_path, commit_message=None):
        """
        Update the contents of a Tool Shed repository with specified tar ball.

        :type id: str
        :param id: Encoded repository ID

        :type tar_ball_path: str
        :param tar_ball_path: Path to file containing tar ball to upload.

        :type commit_message: str
        :param commit_message: Commit message used for the underlying Mercurial
          repository backing Tool Shed repository.

        :rtype: dict
        :return: Returns a dictionary that includes repository content warnings.
          Most valid uploads will result in no such warning and an exception
          will be raised generally if there are problems.
          For example a successful upload will look like::

            {u'content_alert': u'',
             u'message': u''}

        .. versionadded:: 0.5.2
        """
        url = '/'.join([self.gi._make_url(self, id), 'changeset_revision'])
        payload = {
            'file': attach_file(tar_ball_path)
        }
        if commit_message is not None:
            payload['commit_message'] = commit_message
        try:
            return self._post(payload=payload, files_attached=True, url=url)
        finally:
            payload['file'].close()

    def create_repository(self, name, synopsis, description=None,
                          type='unrestricted', remote_repository_url=None,
                          homepage_url=None, category_ids=None):
        """
        Create a new repository in a Tool Shed.

        :type name: str
        :param name: Name of the repository

        :type synopsis: str
        :param synopsis: Synopsis of the repository

        :type description: str
        :param description: Optional description of the repository

        :type type: str
        :param type: type of the repository. One of "unrestricted",
          "repository_suite_definition", or "tool_dependency_definition"

        :type remote_repository_url: str
        :param remote_repository_url: Remote URL (e.g. GitHub/Bitbucket
          repository)

        :type homepage_url: str
        :param homepage_url: Upstream's homepage for the project

        :type category_ids: list
        :param category_ids: List of encoded category IDs

        :rtype: dict
        :return: a dictionary containing information about the new repository.
          For example::

            {"deleted": false,
             "deprecated": false,
             "description": "new_synopsis",
             "homepage_url": "https://github.com/galaxyproject/",
             "id": "8cf91205f2f737f4",
             "long_description": "this is some repository",
             "model_class": "Repository",
             "name": "new_repo_17",
             "owner": "qqqqqq",
             "private": false,
             "remote_repository_url": "https://github.com/galaxyproject/tools-devteam",
             "times_downloaded": 0,
             "type": "unrestricted",
             "user_id": "adb5f5c93f827949"}
        """
        payload = {
            'name': name,
            'synopsis': synopsis,
        }
        if description is not None:
            payload['description'] = description
        if description is not None:
            payload['description'] = description
        if type is not None:
            payload['type'] = type
        if remote_repository_url is not None:
            payload['remote_repository_url'] = remote_repository_url
        if homepage_url is not None:
            payload['homepage_url'] = homepage_url
        if category_ids is not None:
            payload['category_ids[]'] = category_ids
        return self._post(payload)
