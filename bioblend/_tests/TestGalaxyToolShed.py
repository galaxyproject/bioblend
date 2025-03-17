""" """

import os
from typing import Any

from bioblend.galaxy.tools.inputs import (
    conditional,
    dataset,
    inputs,
    repeat,
)
from . import (
    GalaxyTestBase,
    test_util,
)


class TestGalaxyToolShed(GalaxyTestBase.GalaxyTestBase):
    def test_install(self):
        for revision in ['52fbe4eb7ce7', '61acf8a76396', '6b8580e02e99', 'bd518ee51da5', 'c14c7fd4d1be']:
            response = self.gi.toolshed.install_repository_revision(
                "https://toolshed.g2.bx.psu.edu/",
                "ampvis2_alpha_diversity",
                "iuc",
                revision
            )
            assert isinstance(response, list), str(response)
            assert len(response) == 1
            assert response[0]["status"] == 'Installed'

        for revision in ['289d6299bd2e', '77000428c613']:
            response = self.gi.toolshed.install_repository_revision(
                "https://toolshed.g2.bx.psu.edu/",
                "ampvis2_alpha_diversity",
                "iuc",
                revision
            )
            assert isinstance(response, list), str(response)
            assert len(response) == 1
            assert response[0]["status"] == 'Installed'
