"""
Contains interactions dealing with Galaxy container resolvers.
"""
from typing import (
    List,
    Optional,
)

from bioblend.galaxy.client import Client


class ContainerResolutionClient(Client):
    module = "container_resolvers"

    def get_container_resolvers(self) -> list:
        """GET /api/container_resolvers"""
        url = self._make_url()
        return self._get(url=url)

    def show_container_resolver(self, index: int) -> dict:
        """GET /api/container_resolvers/<index>"""
        url = f"{self._make_url()}/{index}"
        return self._get(url=url)

    def resolve(
        self,
        index: Optional[int] = None,
        tool_id: Optional[str] = None,
        resolver_type: Optional[str] = None,
        container_type: Optional[str] = None,
        requirements_only: bool = False,
        install: bool = False,
    ) -> dict:
        """
        Resolve described requirement against specified container resolvers.

        :type index: int
        :param index: index of the dependency resolver with respect to
            the dependency resolvers config file

        :type tool_id: str
        :param tool_id: tool id to resolve against containers

        :type resolver_type: str
        :param resolver_type: restrict to specified resolver type

        :type container_type: str
        :param container_type: restrict to specified container type

        :type requirements_only: bool
        :param requirements_only: ignore tool containers, properties - just search based on tool requirements set to True to mimic default behavior of tool dependency API.

        :type install: bool
        :param install: allow installation of new containers (for build_mulled containers) the way job resolution will operate, defaults to False

        :rtype: dict
        TODO: example
        """
        params = {}
        if tool_id:
            params["tool_id"] = tool_id
        if resolver_type:
            params["resolver_type"] = resolver_type
        if container_type:
            params["container_type"] = container_type
        params["requirements_only"] = requirements_only
        params["install"] = install
        if index is not None:
            url = "/".join((self._make_url(), str(index), "resolve"))
        else:
            url = "/".join((self._make_url(), "resolve"))
        return self._get(url=url, params=params)

    def resolve_toolbox(
        self,
        index: Optional[int] = None,
        tool_ids: Optional[List[str]] = None,
        resolver_type: Optional[str] = None,
        container_type: Optional[str] = None,
        requirements_only: bool = False,
        install: bool = False,
    ) -> dict:
        """
        Apply resolve() to each tool in the toolbox and return the results as a list.
        See documentation for resolve() for a description of parameters that can be
        consumed and a description of the resulting items.

        :type index: int
        :param index: index of the dependency resolver with respect to
            the dependency resolvers config file

        :type tool_ids: list
        :param tool_ids: tool_ids to filter toolbox on

        :type resolver_type: str
        :param resolver_type: restrict to specified resolver type

        :type container_type: str
        :param container_type: restrict to specified container type

        :type requirements_only: bool
        :param requirements_only: ignore tool containers, properties - just search based on tool requirements set to True to mimic default behavior of tool dependency API.

        :type install: bool
        :param install: allow installation of new containers (for build_mulled containers) the way job resolution will operate, defaults to False

        :rtype: dict
        TODO: example
        """
        params = {}
        if tool_ids:
            params["tool_ids"] = ",".join(tool_ids)
        if resolver_type:
            params["resolver_type"] = resolver_type
        if container_type:
            params["container_type"] = container_type
        params["requirements_only"] = str(requirements_only)
        params["install"] = str(install)
        if index is not None:
            url = "/".join((self._make_url(), str(index), "toolbox"))
        else:
            url = "/".join((self._make_url(), "toolbox"))
        return self._get(url=url, params=params)

    def resolve_toolbox_with_install(
        self,
        index: Optional[int] = None,
        tool_ids: Optional[List[str]] = None,
        resolver_type: Optional[str] = None,
        container_type: Optional[str] = None,
        requirements_only: bool = False,
        install: bool = False,
    ) -> list:
        """
        Do the resolution of dependencies like resolve_toolbox(), but allow building and installing new containers.

        :type index: int
        :param index: index of the dependency resolver with respect to
            the dependency resolvers config file

        :type tool_ids: list
        :param tool_ids: tool_ids to filter toolbox on

        :type resolver_type: str
        :param resolver_type: restrict to specified resolver type

        :type container_type: str
        :param container_type: restrict to specified container type

        :type requirements_only: bool
        :param requirements_only: ignore tool containers, properties - just search based on tool requirements set to True to mimic default behavior of tool dependency API.

        :type install: bool
        :param install: allow installation of new containers (for build_mulled* containers) the way job resolution will operate, defaults to False

        :rtype: list of dicts
        :returns: dictified descriptions of the dependencies, with attribute
          `dependency_type: None` if no match was found.
          For example::

        [{'requirements': [{'name': 'canu',
                            'specs': [],
                            'type': 'package',
                            'version': '2.2'}],
        'status': {'cacheable': False,
            'container_description': {'identifier': 'docker://quay.io/biocontainers/canu:2.2--ha47f30e_0',
                                    'resolve_dependencies': False,
                                    'shell': '/bin/bash',
                                    'type': 'singularity'},
            'container_resolver': {'builds_on_resolution': False,
                                    'can_uninstall_dependencies': False,
                                    'model_class': 'MulledSingularityContainerResolver',
                                    'resolver_type': 'mulled_singularity'},
            'dependency_type': 'singularity',
            'environment_path': 'docker://quay.io/biocontainers/canu:2.2--ha47f30e_0',
            'exact': True,
            'model_class': 'ContainerDependency',
            'name': None,
            'version': None},
        'tool_id': 'toolshed.g2.bx.psu.edu/repos/bgruening/canu/canu/2.2+galaxy0'}]
        """
        params = {}
        if tool_ids:
            params["tool_ids"] = ",".join(tool_ids)
        if resolver_type:
            params["resolver_type"] = resolver_type
        if container_type:
            params["container_type"] = container_type
        params["requirements_only"] = str(requirements_only)
        if index is not None:
            url = "/".join((self._make_url(), str(index), "toolbox", "install"))
        else:
            url = "/".join((self._make_url(), "toolbox", "install"))
        return self._post(url=url, payload=params)
