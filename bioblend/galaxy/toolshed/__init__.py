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
        return Client._get(self).json()

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
        return Client._get(self, id=toolShed_id).json()

    def install_repository_revision(self, tool_shed_url, name, owner,
                                    changeset_revision,
                                    install_tool_dependencies=False,
                                    install_repository_dependencies=False,
                                    tool_panel_section_id=None,
                                    new_tool_panel_section_label=None):
        """
        Install a specified repository revision from a specified Tool Shed into
        this Galaxy instance. This example demonstrates installation of a repository
        that contains valid tools, loading them into a section of the Galaxy tool
        panel or creating a new tool panel section.
        You can choose if tool dependencies or repository dependencies should be
        installed, use ``install_tool_dependencies`` or ``install_repository_dependencies``.

        Installing the repository into an existing tool panel section requires
        the tool panel config file (e.g., tool_conf.xml, shed_tool_conf.xml, etc)
        to contain the given tool panel section:

            <section id="from_test_tool_shed" name="From Test Tool Shed" version="">
            </section>

        :type tool_shed_url: string
        :param tool_shed_url: URL of the Tool Shed from which the repository should
                              be installed from (e.g., ``http://testtoolshed.g2.bx.psu.edu``)

        :type name: string
        :param name: The name of the repository that should be installed

        :type owner: string
        :param owner: The name of the repository owner

        :type changeset_revision: string
        :param changeset_revision: The revision of the repository to be installed

        :type install_tool_dependencies: Boolean
        :param install_tool_dependencies: Whether or not to automatically handle
                                          tool dependencies (see
                                          http://wiki.galaxyproject.org/AToolOrASuitePerRepository
                                          for more details)

        :type install_repository_dependencies: Boolean
        :param install_repository_dependencies: Whether or not to automatically
                                                handle repository dependencies
                                                (see http://wiki.galaxyproject.org/DefiningRepositoryDependencies
                                                for more details)

        :type tool_panel_section_id: string
        :param tool_panel_section_id: The ID of the Galaxy tool panel section
                                      where the tool should be insterted under.
                                      Note that you should specify either this
                                      parameter or the ``new_tool_panel_section_label``.
                                      If both are specified, this one will take
                                      precedence.

        :type new_tool_panel_section_label: string
        :param new_tool_panel_section_label: The name of a Galaxy tool panel section
                                             that should be created and the repository
                                             installed into.
        """
        payload = {}
        payload['tool_shed_url'] = tool_shed_url
        payload['name'] = name
        payload['owner'] = owner
        payload['changeset_revision'] = changeset_revision
        payload['install_tool_dependencies'] = install_tool_dependencies
        payload['install_repository_dependencies'] = install_repository_dependencies
        if tool_panel_section_id:
            payload['tool_panel_section_id'] = tool_panel_section_id
        elif new_tool_panel_section_label:
            payload['new_tool_panel_section_label'] = new_tool_panel_section_label

        url = "%s%s" % (self.gi.url, '/tool_shed_repositories/new/install_repository_revision')

        return Client._post(self, url=url, payload=payload)
