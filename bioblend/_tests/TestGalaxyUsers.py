import bioblend.galaxy
from . import (
    GalaxyTestBase,
    test_util,
)


class TestGalaxyUsers(GalaxyTestBase.GalaxyTestBase):
    def test_get_users(self):
        users = self.gi.users.get_users()
        for user in users:
            assert user["id"] is not None
            assert user["email"] is not None

    def test_show_user(self):
        current_user = self.gi.users.get_current_user()
        user = self.gi.users.show_user(current_user["id"])
        assert user["id"] == current_user["id"]
        assert user["username"] == current_user["username"]
        assert user["email"] == current_user["email"]
        # The 2 following tests randomly fail

    #        assert user["nice_total_disk_usage"] == current_user["nice_total_disk_usage"]
    #        assert user["total_disk_usage"] == current_user["total_disk_usage"]

    def test_create_remote_user(self):
        # WARNING: only admins can create users!
        # WARNING: Users cannot be purged through the Galaxy API, so execute
        # this test only on a disposable Galaxy instance!
        if not self.gi.config.get_config()["use_remote_user"]:
            self.skipTest("This Galaxy instance is not configured to use remote users")
        new_user_email = "newuser@example.org"
        user = self.gi.users.create_remote_user(new_user_email)
        assert user["email"] == new_user_email
        if self.gi.config.get_config()["allow_user_deletion"]:
            deleted_user = self.gi.users.delete_user(user["id"])
            assert deleted_user["email"] == new_user_email
            assert deleted_user["deleted"]

    def test_create_local_user(self):
        # WARNING: only admins can create users!
        # WARNING: Users cannot be purged through the Galaxy API, so execute
        # this test only on a disposable Galaxy instance!
        if self.gi.config.get_config()["use_remote_user"]:
            self.skipTest("This Galaxy instance is not configured to use local users")
        new_user_email = "newuser@example.org"
        username = "newuser"
        password = "secret"
        user = self.gi.users.create_local_user(username, new_user_email, password)
        assert user["username"] == username
        assert user["email"] == new_user_email
        # test a BioBlend GalaxyInstance can be created using username+password
        user_gi = bioblend.galaxy.GalaxyInstance(url=self.gi.base_url, email=new_user_email, password=password)
        assert user_gi.users.get_current_user()["email"] == new_user_email
        # test deletion
        if self.gi.config.get_config()["allow_user_deletion"]:
            deleted_user = self.gi.users.delete_user(user["id"])
            assert deleted_user["email"] == new_user_email
            assert deleted_user["deleted"]

    def test_get_current_user(self):
        user = self.gi.users.get_current_user()
        assert user["id"] is not None
        assert user["username"] is not None
        assert user["email"] is not None
        assert user["nice_total_disk_usage"] is not None
        assert user["total_disk_usage"] is not None

    def test_update_user(self):
        # WARNING: only admins can create users!
        # WARNING: Users cannot be purged through the Galaxy API, so execute
        # this test only on a disposable Galaxy instance!
        if self.gi.config.get_config()["use_remote_user"]:
            self.skipTest("This Galaxy instance is not configured to use local users")
        new_user_email = "newuser2@example.org"
        user = self.gi.users.create_local_user("newuser2", new_user_email, "secret")
        assert user["username"] == "newuser2"
        assert user["email"] == new_user_email

        updated_user_email = "updateduser@example.org"
        updated_username = "updateduser"
        user_id = user["id"]
        self.gi.users.update_user(user_id, username=updated_username, email=updated_user_email)
        user = self.gi.users.show_user(user_id)
        assert user["username"] == updated_username
        assert user["email"] == updated_user_email

        if self.gi.config.get_config()["allow_user_deletion"]:
            self.gi.users.delete_user(user["id"])

    def test_get_user_apikey(self):
        user_id = self.gi.users.get_current_user()["id"]
        assert self.gi.users.get_user_apikey(user_id)

    @test_util.skip_unless_galaxy("release_21.01")
    def test_get_or_create_user_apikey(self):
        user_id = self.gi.users.get_current_user()["id"]
        assert self.gi.users.get_or_create_user_apikey(user_id)
