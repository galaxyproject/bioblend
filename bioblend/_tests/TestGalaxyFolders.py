from typing import (
    Dict,
    List,
)

from . import (
    GalaxyTestBase,
    test_util,
)

FOO_DATA = "foo\nbar\n"


class TestGalaxyFolders(GalaxyTestBase.GalaxyTestBase):
    def setUp(self):
        super().setUp()
        self.name = "automated test folder"
        self.library = self.gi.libraries.create_library(
            self.name, description="automated test", synopsis="automated test synopsis"
        )
        self.folder = self.gi.folders.create_folder(
            self.library["root_folder_id"], self.name, description="automatically created folder"
        )

    def tearDown(self):
        self.gi.libraries.delete_library(self.library["id"])

    def test_create_folder(self):
        assert self.folder["name"] == self.name
        assert self.folder["description"] == "automatically created folder"

    def test_show_folder(self):
        f2 = self.gi.folders.show_folder(self.folder["id"])
        assert f2["id"] == self.folder["id"]

    def test_show_folder_contents(self):
        f2 = self.gi.folders.show_folder(self.folder["id"], contents=True)
        assert "folder_contents" in f2
        assert "metadata" in f2
        assert self.name == f2["metadata"]["folder_name"]

    @test_util.skip_unless_galaxy("release_21.05")
    def test_show_folder_contents_limit(self):
        subfolders = [self.gi.folders.create_folder(self.folder["id"], f"{self.name} {i}") for i in range(12)]

        # check defaults for limit and offset
        f2 = self.gi.folders.show_folder(self.folder["id"], contents=True)
        assert len(f2["folder_contents"]) == 10
        assert f2["folder_contents"][0]["name"] == f"{self.name} 0"

        # check non defaults
        f2 = self.gi.folders.show_folder(self.folder["id"], contents=True, limit=1, offset=1)
        assert len(f2["folder_contents"]) == 1
        assert f2["folder_contents"][0]["name"] == f"{self.name} 1"

    def test_delete_folder(self):
        self.sub_folder = self.gi.folders.create_folder(self.folder["id"], self.name)
        self.gi.folders.delete_folder(self.sub_folder["id"])

    def test_update_folder(self):
        self.folder = self.gi.folders.update_folder(self.folder["id"], "new-name", "new-description")
        assert self.folder["name"] == "new-name"
        assert self.folder["description"] == "new-description"

    def test_get_set_permissions(self):
        empty_permission: Dict[str, List] = {
            "add_library_item_role_list": [],
            "modify_folder_role_list": [],
            "manage_folder_role_list": [],
        }
        # They should be empty to start with
        assert self.gi.folders.get_permissions(self.folder["id"], scope="current") == empty_permission
        assert self.gi.folders.get_permissions(self.folder["id"], scope="available") == empty_permission
        # Then we'll add a role
        role = self.gi.roles.get_roles()[0]
        self.gi.folders.set_permissions(self.folder["id"], add_ids=[role["id"]])
        assert (
            role["id"]
            in self.gi.folders.get_permissions(self.folder["id"], scope="available")["add_library_item_role_list"][0]
        )
