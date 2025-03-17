""" """

from . import GalaxyTestBase


class TestGalaxyToolShed(GalaxyTestBase.GalaxyTestBase):

    def test_install_old_first(self):
        # test uses two revisions where the tool version has not been bumped
        # 6:289d6299bd2e, 7:c14c7fd4d1be has not been bumped

        # asking to install old version immediately installs
        # new version
        response = self.gi.toolshed.install_repository_revision(
            tool_shed_url="https://toolshed.g2.bx.psu.edu/",
            name="ampvis2_alpha_diversity",
            owner="iuc",
            changeset_revision="289d6299bd2e",
        )
        assert isinstance(response, list), str(response)
        assert len(response) == 1
        assert response[0]["status"] == 'Installed'

        installed_repos = self.gi.toolshed.get_repositories()
        assert len(installed_repos) == 1
        assert installed_repos[0]['installed_changeset_revision'] == 'c14c7fd4d1be'
        assert installed_repos[0]['changeset_revision'] == 'c14c7fd4d1be'

        self.gi.toolshed.uninstall_repository_revision(
            name="ampvis2_alpha_diversity",
            owner="iuc",
            changeset_revision="c14c7fd4d1be",
            tool_shed_url="https://toolshed.g2.bx.psu.edu/",
            remove_from_disk=True,
        )

    def test_install_new_first(self):
        # 6:289d6299bd2e
        # 7:c14c7fd4d1be has not been bumped
        response = self.gi.toolshed.install_repository_revision(
            tool_shed_url="https://toolshed.g2.bx.psu.edu/",
            name="ampvis2_alpha_diversity",
            owner="iuc",
            changeset_revision="c14c7fd4d1be",
        )
        assert isinstance(response, list), str(response)
        assert len(response) == 1
        assert response[0]["status"] == 'Installed'

        installed_repos = self.gi.toolshed.get_repositories()
        assert len(installed_repos) == 1
        assert installed_repos[0]['installed_changeset_revision'] == 'c14c7fd4d1be'
        assert installed_repos[0]['changeset_revision'] == 'c14c7fd4d1be'

        # install older revision
        # -> galaxy realizes that a tool with the same version is alredy installed
        # -> responds with a dict indicating this
        response = self.gi.toolshed.install_repository_revision(
            tool_shed_url="https://toolshed.g2.bx.psu.edu/",
            name="ampvis2_alpha_diversity",
            owner="iuc",
            changeset_revision="289d6299bd2e",
        )
        assert isinstance(response, dict), str(response)
        assert response["status"] == 'ok'

        installed_repos = self.gi.toolshed.get_repositories()
        assert len(installed_repos) == 1
        assert installed_repos[0]['installed_changeset_revision'] == 'c14c7fd4d1be'
        assert installed_repos[0]['changeset_revision'] == 'c14c7fd4d1be'

        self.gi.toolshed.uninstall_repository_revision(
            name="ampvis2_alpha_diversity",
            owner="iuc",
            changeset_revision="c14c7fd4d1be",
            tool_shed_url="https://toolshed.g2.bx.psu.edu/",
            remove_from_disk=True,
        )
